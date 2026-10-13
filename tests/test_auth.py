"""
Login and role checks. The chore tracker has no accounts of its own: it
asks the family login API who a bearer token belongs to (mocked here via
chores.auth.fetch_identity).
"""
import os
from unittest.mock import patch, MagicMock

import pytest
import requests

from chores import create_app
from chores.database import db
from chores.models.user import User
from chores.models.chore import Chore
from chores.models.completion import Completion

import chores.routes.v1.user_routes  # noqa: F401

PENNY_PM_ID, DOM_PM_ID = 21, 22

PARENT = {"role": "parent", "child_id": None, "child_name": None}
ADMIN = {"role": "admin", "child_id": None, "child_name": None}
ADULT = {"role": "adult", "child_id": None, "child_name": None}
PENNY = {"role": "child", "child_id": PENNY_PM_ID, "child_name": "Penelope"}
UNLINKED_CHILD = {"role": "child", "child_id": None, "child_name": None}


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
def ids(app):
    """Two children with one pending completion each, plus a chore and a
    user with no history (deleting ones that have history is a separate,
    existing problem)."""
    with app.app_context():
        penny = User(name="Penelope", email="p@home.com",
                     pm_child_id=PENNY_PM_ID)
        dom = User(name="Dominic", email="d@home.com",
                   pm_child_id=DOM_PM_ID)
        spare = User(name="Spare", email="s@home.com")
        dishes = Chore(task_name="Dishes", reward_level=2.00)
        unused = Chore(task_name="Unused", reward_level=1.00)
        db.session.add_all([penny, dom, spare, dishes, unused])
        db.session.commit()
        db.session.add_all([
            Completion(user_id=penny.id, chore_id=dishes.id),
            Completion(user_id=dom.id, chore_id=dishes.id)])
        db.session.commit()
        return {"penny": penny.id, "dom": dom.id, "spare": spare.id,
                "chore": dishes.id, "unused": unused.id}


@pytest.fixture()
def call(app):
    """call(identity, method, path, **kw): one request as that login.
    identity=None sends no token, a (status, None) tuple makes the login
    API answer with that status, and an exception makes it unreachable."""
    def _call(identity, method, path, **kwargs):
        client = app.test_client()
        headers = {} if identity is None else {
            "Authorization": "Bearer test-token"}
        if isinstance(identity, Exception):
            mock = {"side_effect": identity}
        elif isinstance(identity, tuple):
            mock = {"return_value": identity}
        else:
            mock = {"return_value": (200, identity)}
        with patch("chores.auth.fetch_identity", **mock):
            return getattr(client, method)(path, headers=headers, **kwargs)
    return _call


def routes(ids):
    """(method, path, kwargs, parents_only) for every route, acting on
    Penelope where a user is involved. The deletes come last so the
    earlier calls still have something to act on."""
    p, c = ids["penny"], ids["chore"]
    return [
        ("get", "/api/v1/chores/", {}, False),
        ("post", "/api/v1/chores/",
         {"json": {"task_name": "Hoover", "reward_level": 1}}, True),
        ("post", "/api/v1/chores/complete",
         {"json": {"user_id": p, "chore_id": c}}, False),
        ("put", f"/api/v1/chores/{c}", {"json": {"reward_level": 99}}, True),
        ("post", "/api/v1/users/add_user",
         {"json": {"name": "New", "email": "n@home.com"}}, True),
        ("get", "/api/v1/users/", {}, False),
        ("get", f"/api/v1/users/{p}/balance", {}, False),
        ("get", f"/api/v1/users/{p}/history", {}, False),
        ("post", f"/api/v1/users/{p}/payout", {}, True),
        ("put", f"/api/v1/users/{p}", {"json": {"name": "Penelope"}}, True),
        ("get", "/api/v1/users/test_email", {}, True),
        ("delete", f"/api/v1/users/{ids['spare']}", {}, True),
        ("delete", f"/api/v1/chores/{ids['unused']}", {}, True),
    ]


def test_every_route_needs_a_token(call, ids):
    for method, path, kwargs, _ in routes(ids):
        resp = call(None, method, path, **kwargs)
        assert resp.status_code == 401, (method, path)

    assert call(None, "post",
                f"/api/v1/users/{ids['penny']}/request_payout"
                ).status_code == 401


def test_a_token_the_login_api_rejects_is_401(call, ids):
    resp = call((401, None), "get", "/api/v1/chores/")

    assert resp.status_code == 401


def test_login_api_down_is_503_not_open(call, ids):
    unreachable = requests.exceptions.ConnectionError("down")

    assert call((500, None), "get", "/api/v1/chores/").status_code == 503
    assert call(unreachable, "get", "/api/v1/chores/").status_code == 503


def test_adults_outside_the_household_get_403(call, ids):
    for method, path, kwargs, _ in routes(ids):
        resp = call(ADULT, method, path, **kwargs)
        assert resp.status_code == 403, (method, path)


@pytest.mark.parametrize("identity", [PARENT, ADMIN])
def test_parents_and_admin_can_use_every_route(call, ids, identity):
    with patch("chores.routes.v1.user_routes.send_payout_email",
               return_value=True):
        for method, path, kwargs, _ in routes(ids):
            resp = call(identity, method, path, **kwargs)
            assert resp.status_code in (200, 201), (method, path)


def test_child_is_refused_on_parent_only_routes(call, ids, app):
    for method, path, kwargs, parents_only in routes(ids):
        if parents_only:
            resp = call(PENNY, method, path, **kwargs)
            assert resp.status_code == 403, (method, path)

    with app.app_context():
        assert Chore.query.count() == 2
        assert User.query.count() == 3
        assert db.session.get(Chore, ids["chore"]).reward_level == 2.00


def test_child_can_use_their_own_routes(call, ids):
    for method, path, kwargs, parents_only in routes(ids):
        if not parents_only:
            resp = call(PENNY, method, path, **kwargs)
            assert resp.status_code in (200, 201), (method, path)


def test_child_only_sees_themselves_in_the_user_list(call, ids):
    resp = call(PENNY, "get", "/api/v1/users/")

    assert [u["name"] for u in resp.get_json()] == ["Penelope"]


def test_child_cannot_act_for_a_sibling(call, ids, app):
    dom, chore = ids["dom"], ids["chore"]

    assert call(PENNY, "get",
                f"/api/v1/users/{dom}/balance").status_code == 403
    assert call(PENNY, "get",
                f"/api/v1/users/{dom}/history").status_code == 403
    assert call(PENNY, "post", "/api/v1/chores/complete",
                json={"user_id": dom, "chore_id": chore}).status_code == 403
    assert call(PENNY, "post",
                f"/api/v1/users/{dom}/request_payout").status_code == 403

    with app.app_context():
        assert Completion.query.filter_by(user_id=dom).count() == 1


def test_child_without_a_linked_profile_can_do_nothing_personal(call, ids):
    penny = ids["penny"]

    assert call(UNLINKED_CHILD, "get", "/api/v1/users/").get_json() == []
    assert call(UNLINKED_CHILD, "get",
                f"/api/v1/users/{penny}/balance").status_code == 403
    assert call(UNLINKED_CHILD, "post",
                f"/api/v1/users/{penny}/request_payout").status_code == 403


@patch("chores.routes.v1.user_routes.send_payout_email", return_value=True)
@patch("chores.routes.v1.user_routes.requests.post")
@patch("chores.routes.v1.user_routes.requests.get")
def test_child_can_request_their_own_payout(get_mock, post_mock, mail_mock,
                                            call, ids, app):
    post_mock.return_value = MagicMock()

    resp = call(PENNY, "post",
                f"/api/v1/users/{ids['penny']}/request_payout")

    assert resp.status_code == 200
    assert post_mock.call_count == 1
    with app.app_context():
        statuses = [c.payout_status for c in Completion.query.all()]
        assert sorted(statuses) == ["paid", "pending"]


def test_preflight_requests_are_not_blocked(app):
    resp = app.test_client().options(
        "/api/v1/chores/", headers={
            "Origin": "https://chores.example",
            "Access-Control-Request-Method": "GET"})

    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# The stored Pocket Money link (pm_child_id)
# ---------------------------------------------------------------------------

def test_renaming_a_child_in_either_app_does_not_break_their_login(
        call, ids, app):
    """The link is the Pocket Money child id, so names can drift apart."""
    with app.app_context():
        db.session.get(User, ids["penny"]).name = "Penny the Great"
        db.session.commit()
    renamed_elsewhere = {**PENNY, "child_name": "P. Ford"}

    listed = call(renamed_elsewhere, "get", "/api/v1/users/").get_json()

    assert [u["id"] for u in listed] == [ids["penny"]]
    assert call(renamed_elsewhere, "get",
                f"/api/v1/users/{ids['penny']}/balance").status_code == 200


def test_matching_names_alone_no_longer_link_a_login(call, ids, app):
    with app.app_context():
        db.session.get(User, ids["penny"]).pm_child_id = None
        db.session.commit()

    assert call(PENNY, "get", "/api/v1/users/").get_json() == []
    assert call(PENNY, "get",
                f"/api/v1/users/{ids['penny']}/balance").status_code == 403


@patch("chores.routes.v1.user_routes.requests.post")
def test_payout_for_an_unlinked_user_is_refused_and_stays_pending(
        post_mock, call, ids, app):
    resp = call(PARENT, "post", f"/api/v1/users/{ids['spare']}/request_payout")
    assert resp.status_code == 409

    with app.app_context():
        db.session.get(User, ids["penny"]).pm_child_id = None
        db.session.commit()
    resp = call(PARENT, "post", f"/api/v1/users/{ids['penny']}/request_payout")

    assert resp.status_code == 409
    assert "Not linked" in resp.get_json()["error"]
    assert post_mock.call_count == 0
    with app.app_context():
        statuses = {c.payout_status for c in Completion.query.filter_by(
            user_id=ids["penny"]).all()}
        assert statuses == {"pending"}


def test_parent_can_set_change_and_clear_a_link(call, ids, app):
    spare = ids["spare"]

    def link():
        users = call(PARENT, "get", "/api/v1/users/").get_json()
        return next(u["pm_child_id"] for u in users if u["id"] == spare)

    assert link() is None
    assert call(PARENT, "put", f"/api/v1/users/{spare}",
                json={"pm_child_id": 30}).status_code == 200
    assert link() == 30
    # Editing something else leaves the link alone
    assert call(PARENT, "put", f"/api/v1/users/{spare}",
                json={"name": "Spare Two"}).status_code == 200
    assert link() == 30
    assert call(PARENT, "put", f"/api/v1/users/{spare}",
                json={"pm_child_id": None}).status_code == 200
    assert link() is None


def test_a_pocket_money_account_can_only_be_linked_once(call, ids):
    resp = call(PARENT, "put", f"/api/v1/users/{ids['spare']}",
                json={"pm_child_id": PENNY_PM_ID})

    assert resp.status_code == 409


def test_link_must_be_a_number(call, ids):
    resp = call(PARENT, "put", f"/api/v1/users/{ids['spare']}",
                json={"pm_child_id": "Penelope"})

    assert resp.status_code == 400


def test_new_user_can_be_created_with_a_link(call, ids):
    resp = call(PARENT, "post", "/api/v1/users/add_user", json={
        "name": "Third", "email": "t@home.com", "pm_child_id": 40})

    assert resp.status_code == 201
    users = call(PARENT, "get", "/api/v1/users/").get_json()
    assert next(u for u in users if u["name"] == "Third")["pm_child_id"] == 40


def test_child_cannot_change_their_own_link(call, ids):
    resp = call(PENNY, "put", f"/api/v1/users/{ids['penny']}",
                json={"pm_child_id": DOM_PM_ID})

    assert resp.status_code == 403


def test_existing_database_gets_the_new_column(tmp_path, monkeypatch):
    """A database created before pm_child_id existed is upgraded on start
    and keeps its rows; starting again is a no-op."""
    import sqlite3
    path = tmp_path / "old.db"
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE user (id INTEGER PRIMARY KEY, name VARCHAR(100) NOT NULL,
                           email VARCHAR(120) NOT NULL UNIQUE);
        INSERT INTO user (name, email) VALUES ('Penelope', 'p@home.com');
    """)
    con.commit()
    con.close()
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{path}")
    import importlib
    import config
    importlib.reload(config)

    for _ in range(2):
        old_app = create_app(config.Config)
        with old_app.app_context():
            user = User.query.one()
            assert (user.name, user.pm_child_id) == ("Penelope", None)
            db.engine.dispose()

    monkeypatch.delenv("DATABASE_URL")
    importlib.reload(config)
