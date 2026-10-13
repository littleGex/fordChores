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

PARENT = {"role": "parent", "child_name": None}
ADMIN = {"role": "admin", "child_name": None}
ADULT = {"role": "adult", "child_name": None}
PENNY = {"role": "child", "child_name": "Penelope"}
UNLINKED_CHILD = {"role": "child", "child_name": None}


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
        penny = User(name="Penelope", email="p@home.com")
        dom = User(name="Dominic", email="d@home.com")
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
    lookup = MagicMock()
    lookup.raise_for_status.return_value = None
    lookup.json.return_value = {"id": 7}
    get_mock.return_value = lookup
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
