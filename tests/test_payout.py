"""
Tests for the double-payout fix.

Covers three endpoints/functions, all of which previously suffered from
a read-pending -> (slow work) -> mark-paid race that allowed duplicate
button presses / concurrent requests to pay out the same completions
more than once:

  - POST /api/v1/users/<id>/request_payout  (syncs with PocketMoney)
  - POST /api/v1/users/<id>/payout          (local-only payout)
  - chores.database.payout_manager.run_weekly_payout

Test strategy
--------------
1. Sequential idempotency tests (DB-agnostic): call the endpoint/function
   twice in a row and assert the second call is a no-op. This exercises
   the "claim before doing work" logic and works on SQLite too, because
   each call commits before the next one starts (no real concurrency
   needed to prove idempotency of the *status flip*).

2. Concurrency test (Postgres only): fires two real concurrent requests
   at /request_payout using threads + a WSGI test client, and asserts
   the external "deposit" call (mocked) only happens once. This exercises
   the `with_for_update(skip_locked=True)` row locking, which requires
   Postgres (SQLite does not support SELECT ... FOR UPDATE).

   These tests are marked and skipped automatically if the configured
   DB is SQLite, since `with_for_update` will raise on SQLite.

Run with:
    cd chores
    python -m pytest tests/test_payout_idempotency.py -v

For the concurrency test, point DATABASE_URL at a real Postgres instance,
e.g. the one from docker-compose:
    DATABASE_URL=postgresql://postgres:postgres@localhost:5432/chores_test \
        python -m pytest tests/test_payout_idempotency.py -v
"""

import os
import threading
from unittest.mock import patch, MagicMock

import pytest

from chores import create_app
from chores.database import db
from chores.database.payout_manager import run_weekly_payout
from chores.models.user import User
from chores.models.chore import Chore
from chores.models.completion import Completion

# Explicitly import the user_routes submodule. mock.patch resolves dotted
# paths like "chores.routes.v1.user_routes.requests" via getattr() traversal,
# which requires chores.routes.v1.user_routes to already be bound as an
# attribute of the chores.routes package. If chores/routes/__init__.py
# doesn't itself import/expose this submodule, that getattr() fails with
# "module 'chores.routes' has no attribute 'user_routes'" even though the
# module is otherwise importable. Importing it here ensures it's bound.
import chores.routes.v1.user_routes  # noqa: F401


IS_SQLITE = "sqlite" in (
    os.getenv("DATABASE_URL", "sqlite://")
).lower()


@pytest.fixture()
def app():
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=os.getenv(
            "DATABASE_URL", "sqlite:///:memory:"
        ),
    )

    with app.app_context():
        db.drop_all()
        db.create_all()

    yield app

    with app.app_context():
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def seeded_user(app):
    """Create a user with two pending completions worth 7.00 total."""
    with app.app_context():
        user = User(name="Alex", email="alex@home.com")
        dishes = Chore(task_name="Dishes", reward_level=2.00)
        mow = Chore(task_name="Mow Lawn", reward_level=5.00)

        db.session.add_all([user, dishes, mow])
        db.session.commit()

        c1 = Completion(user_id=user.id,
                        chore_id=dishes.id,
                        payout_status='pending')
        c2 = Completion(user_id=user.id,
                        chore_id=mow.id,
                        payout_status='pending')
        db.session.add_all([c1, c2])
        db.session.commit()

        return user.id


# ---------------------------------------------------------------------------
# run_weekly_payout / POST /payout
# ---------------------------------------------------------------------------

def test_run_weekly_payout_pays_pending_total(app, seeded_user):
    with app.app_context():
        total = run_weekly_payout(seeded_user)
        assert total == 7.00

        statuses = {c.id: c.payout_status for c in Completion.query.filter_by(
                         user_id=seeded_user).all()}
        assert all(s == 'paid' for s in statuses.values())


def test_run_weekly_payout_second_call_is_noop(app, seeded_user):
    """Calling run_weekly_payout twice must not double-count the total."""
    with app.app_context():
        first = run_weekly_payout(seeded_user)
        second = run_weekly_payout(seeded_user)

        assert first == 7.00
        assert second == 0.0  # nothing left to pay


def test_payout_endpoint_double_post_is_noop(client, seeded_user):
    """
    Simulates a double button-press on POST /payout: the second call
    should report status 'noop' and amount_paid 0.0, not pay again.
    """
    resp1 = client.post(f"/api/v1/users/{seeded_user}/payout")
    assert resp1.status_code == 200
    assert resp1.get_json()["amount_paid"] == 7.00
    assert resp1.get_json()["status"] == "success"

    resp2 = client.post(f"/api/v1/users/{seeded_user}/payout")
    assert resp2.status_code == 200
    assert resp2.get_json()["amount_paid"] == 0.0
    assert resp2.get_json()["status"] == "noop"


# ---------------------------------------------------------------------------
# POST /request_payout (PocketMoney-syncing route)
# ---------------------------------------------------------------------------

def _mock_pocketmoney(get_mock, post_mock, pm_child_id="pm-123"):
    lookup_response = MagicMock()
    lookup_response.raise_for_status.return_value = None
    lookup_response.json.return_value = {"id": pm_child_id}
    get_mock.return_value = lookup_response

    deposit_response = MagicMock()
    deposit_response.raise_for_status.return_value = None
    post_mock.return_value = deposit_response


@patch("chores.routes.v1.user_routes.send_payout_email", return_value=True)
@patch("chores.routes.v1.user_routes.requests.post")
@patch("chores.routes.v1.user_routes.requests.get")
def test_request_payout_calls_pocketmoney_once(
    get_mock, post_mock, mail_mock, client, seeded_user
):
    _mock_pocketmoney(get_mock, post_mock)

    resp = client.post(f"/api/v1/users/{seeded_user}/request_payout")

    assert resp.status_code == 200
    assert resp.get_json()["message"] == "Payout processed"
    assert post_mock.call_count == 1

    # Deposit amount should be the full pending total
    _, kwargs = post_mock.call_args
    assert kwargs["params"]["amount"] == 7.00


@patch("chores.routes.v1.user_routes.send_payout_email", return_value=True)
@patch("chores.routes.v1.user_routes.requests.post")
@patch("chores.routes.v1.user_routes.requests.get")
def test_request_payout_double_post_does_not_double_charge(
    get_mock, post_mock, mail_mock, client, seeded_user
):
    """
    Simulates the reported bug: the request_payout button is pressed
    twice in a row. The second call must not trigger a second deposit.
    """
    _mock_pocketmoney(get_mock, post_mock)

    resp1 = client.post(f"/api/v1/users/{seeded_user}/request_payout")
    resp2 = client.post(f"/api/v1/users/{seeded_user}/request_payout")

    assert resp1.status_code == 200
    assert resp1.get_json()["message"] == "Payout processed"

    assert resp2.status_code == 200
    assert resp2.get_json()["message"] == "No pending chores"

    # PocketMoney deposit should only have been called once, total
    assert post_mock.call_count == 1


@patch("chores.routes.v1.user_routes.send_payout_email", return_value=True)
@patch("chores.routes.v1.user_routes.requests.post")
@patch("chores.routes.v1.user_routes.requests.get")
def test_request_payout_rolls_back_on_pocketmoney_failure(
    get_mock, post_mock, mail_mock, app, client, seeded_user
):
    """If the PocketMoney call fails, completions go back to 'pending'
    so they can be retried, rather than being lost in 'processing'."""
    import requests as requests_module

    lookup_response = MagicMock()
    lookup_response.raise_for_status.return_value = None
    lookup_response.json.return_value = {"id": "pm-123"}
    get_mock.return_value = lookup_response

    post_mock.side_effect = requests_module.exceptions.ConnectionError(
        "boom"
    )

    resp = client.post(f"/api/v1/users/{seeded_user}/request_payout")
    assert resp.status_code == 503

    with app.app_context():
        statuses = {c.payout_status for c in Completion.query.filter_by(
            user_id=seeded_user).all()}
        assert statuses == {"pending"}


# ---------------------------------------------------------------------------
# Concurrency test (Postgres only - requires real row locking)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    IS_SQLITE,
    reason="with_for_update(skip_locked=True) requires Postgres; "
           "set DATABASE_URL to a Postgres instance to run this test."
)
@patch("chores.routes.v1.user_routes.send_payout_email", return_value=True)
@patch("chores.routes.v1.user_routes.requests.post")
@patch("chores.routes.v1.user_routes.requests.get")
def test_request_payout_concurrent_double_click(
    get_mock, post_mock, mail_mock, app, seeded_user
):
    """
    Fires two genuinely concurrent /request_payout requests (simulating
    a child mashing the button) and asserts PocketMoney's deposit
    endpoint is only ever called once.
    """
    _mock_pocketmoney(get_mock, post_mock)

    client = app.test_client()
    results = []

    def fire():
        results.append(
            client.post(f"/api/v1/users/{seeded_user}/request_payout")
        )

    t1 = threading.Thread(target=fire)
    t2 = threading.Thread(target=fire)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    messages = sorted(r.get_json()["message"] for r in results)
    assert messages == ["No pending chores", "Payout processed"]
    assert post_mock.call_count == 1
