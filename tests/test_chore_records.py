"""
Records of completed chores: deleting chores and users that have history,
and what a completed chore is worth. Deleting used to fail with a
server error on Postgres (the foreign keys from completion refuse the
delete), which made every chore that had ever been done undeletable.
"""
import os
from unittest.mock import patch

import pytest

from chores import create_app
from chores.database import db
from chores.models.user import User
from chores.models.chore import Chore
from chores.models.completion import Completion

import chores.routes.v1.user_routes  # noqa: F401

PARENT = (200, {"role": "parent", "child_id": None})
KID_PM_ID = 21


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
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    client = app.test_client()
    client.environ_base["HTTP_AUTHORIZATION"] = "Bearer test-token"
    with patch("chores.auth.fetch_identity", return_value=PARENT):
        yield client


@pytest.fixture()
def ids(app):
    """A child with one paid and one pending completion of 'Dishes',
    plus a chore nobody has done and a user with only paid history."""
    with app.app_context():
        kid = User(name="Kid", email="k@home.com", pm_child_id=KID_PM_ID)
        done = User(name="Done", email="d@home.com")
        dishes = Chore(task_name="Dishes", reward_level=2.00)
        unused = Chore(task_name="Unused", reward_level=1.00)
        db.session.add_all([kid, done, dishes, unused])
        db.session.commit()
        db.session.add_all([
            Completion(user_id=kid.id, chore_id=dishes.id,
                       payout_status='paid'),
            Completion(user_id=kid.id, chore_id=dishes.id,
                       payout_status='pending'),
            Completion(user_id=done.id, chore_id=dishes.id,
                       payout_status='paid')])
        db.session.commit()
        return {"kid": kid.id, "done": done.id,
                "dishes": dishes.id, "unused": unused.id}


def chore_names(client):
    return [c["task"] for c in client.get("/api/v1/chores/").get_json()]


class TestDeleteChore:

    def test_chore_nobody_has_done_is_really_deleted(self, client, ids, app):
        resp = client.delete(f"/api/v1/chores/{ids['unused']}")

        assert resp.status_code == 200
        assert resp.get_json()["archived"] is False
        with app.app_context():
            assert db.session.get(Chore, ids["unused"]) is None

    def test_chore_with_history_is_retired_not_deleted(self, client, ids,
                                                       app):
        resp = client.delete(f"/api/v1/chores/{ids['dishes']}")

        assert resp.status_code == 200
        assert resp.get_json()["archived"] is True
        assert chore_names(client) == ["Unused"]
        with app.app_context():
            assert db.session.get(Chore, ids["dishes"]).archived is True
            assert Completion.query.count() == 3

    def test_history_and_balance_survive(self, client, ids):
        client.delete(f"/api/v1/chores/{ids['dishes']}")

        history = client.get(f"/api/v1/users/{ids['kid']}/history")
        balance = client.get(f"/api/v1/users/{ids['kid']}/balance")

        assert history.status_code == 200
        assert [h["task"] for h in history.get_json()] == ["Dishes"] * 2
        assert balance.get_json()["pending_balance"] == 2.00

    @patch("chores.routes.v1.user_routes.send_payout_email",
           return_value=True)
    @patch("chores.routes.v1.user_routes.requests.post")
    def test_pending_completion_of_a_retired_chore_still_pays_out(
            self, post_mock, mail_mock, client, ids):
        client.delete(f"/api/v1/chores/{ids['dishes']}")

        resp = client.post(f"/api/v1/users/{ids['kid']}/request_payout")

        assert resp.status_code == 200
        assert post_mock.call_args.kwargs["params"]["amount"] == 2.00

    def test_retired_chore_cannot_be_completed_again(self, client, ids):
        client.delete(f"/api/v1/chores/{ids['dishes']}")

        resp = client.post("/api/v1/chores/complete", json={
            "user_id": ids["kid"], "chore_id": ids["dishes"]})

        assert resp.status_code == 404

    def test_deleting_twice_is_harmless(self, client, ids):
        first = client.delete(f"/api/v1/chores/{ids['dishes']}")
        second = client.delete(f"/api/v1/chores/{ids['dishes']}")

        assert (first.status_code, second.status_code) == (200, 200)

    def test_same_name_can_be_added_again(self, client, ids):
        client.delete(f"/api/v1/chores/{ids['dishes']}")

        resp = client.post("/api/v1/chores/", json={
            "task_name": "Dishes", "reward_level": 3})

        assert resp.status_code == 201
        assert chore_names(client) == ["Unused", "Dishes"]

    def test_unknown_chore_is_404(self, client, ids):
        assert client.delete("/api/v1/chores/99999").status_code == 404


class TestDeleteUser:

    def test_user_with_unpaid_chores_is_refused(self, client, ids, app):
        resp = client.delete(f"/api/v1/users/{ids['kid']}")

        assert resp.status_code == 409
        assert "1 unpaid chore." in resp.get_json()["error"]
        with app.app_context():
            assert db.session.get(User, ids["kid"]) is not None
            assert Completion.query.filter_by(
                user_id=ids["kid"]).count() == 2

    def test_user_with_only_paid_history_is_removed_with_it(
            self, client, ids, app):
        resp = client.delete(f"/api/v1/users/{ids['done']}")

        assert resp.status_code == 200
        with app.app_context():
            assert db.session.get(User, ids["done"]) is None
            assert Completion.query.filter_by(
                user_id=ids["done"]).count() == 0
            # Nobody else's records are touched
            assert Completion.query.filter_by(
                user_id=ids["kid"]).count() == 2
            assert db.session.get(Chore, ids["dishes"]) is not None

    def test_user_can_be_removed_once_paid_out(self, client, ids, app):
        client.post(f"/api/v1/users/{ids['kid']}/payout")

        resp = client.delete(f"/api/v1/users/{ids['kid']}")

        assert resp.status_code == 200
        with app.app_context():
            assert db.session.get(User, ids["kid"]) is None

    def test_removed_users_pocket_money_link_can_be_reused(self, client,
                                                           ids):
        client.post(f"/api/v1/users/{ids['kid']}/payout")
        client.delete(f"/api/v1/users/{ids['kid']}")

        resp = client.post("/api/v1/users/add_user", json={
            "name": "Kid again", "email": "k2@home.com",
            "pm_child_id": KID_PM_ID})

        assert resp.status_code == 201

    def test_unknown_user_is_404(self, client, ids):
        assert client.delete("/api/v1/users/99999").status_code == 404


def test_existing_database_gets_the_archived_column(tmp_path, monkeypatch):
    """A database from before chores could be retired is upgraded on
    start; existing chores stay visible."""
    import importlib
    import sqlite3
    import config
    path = tmp_path / "old.db"
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE chore (id INTEGER PRIMARY KEY,
                            task_name VARCHAR(100) NOT NULL,
                            reward_level FLOAT NOT NULL);
        INSERT INTO chore (task_name, reward_level) VALUES ('Dishes', 2.0);
    """)
    con.commit()
    con.close()
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{path}")
    importlib.reload(config)

    for _ in range(2):
        old_app = create_app(config.Config)
        with old_app.app_context():
            chore = Chore.query.one()
            assert (chore.task_name, chore.archived) == ("Dishes", False)
            db.engine.dispose()

    monkeypatch.delenv("DATABASE_URL")
    importlib.reload(config)


# ---------------------------------------------------------------------------
# What a completed chore is worth is fixed when it is done
# ---------------------------------------------------------------------------

class TestStoredAmount:

    @pytest.fixture()
    def done(self, client, app):
        """Kid completes 'Make bed' at 0.10 through the API."""
        with app.app_context():
            kid = User(name="Kid", email="k@home.com", pm_child_id=KID_PM_ID)
            bed = Chore(task_name="Make bed", reward_level=0.10)
            db.session.add_all([kid, bed])
            db.session.commit()
            ids = {"kid": kid.id, "bed": bed.id}
        resp = client.post("/api/v1/chores/complete", json={
            "user_id": ids["kid"], "chore_id": ids["bed"]})
        assert resp.status_code == 201
        return ids

    def balance(self, client, ids):
        return client.get(
            f"/api/v1/users/{ids['kid']}/balance").get_json()[
                "pending_balance"]

    def history(self, client, ids):
        return [(h["task"], h["reward"]) for h in client.get(
            f"/api/v1/users/{ids['kid']}/history").get_json()]

    @pytest.mark.parametrize("new_reward", [0.20, 0.05])
    def test_editing_a_reward_does_not_change_unpaid_chores(
            self, client, done, new_reward):
        client.put(f"/api/v1/chores/{done['bed']}",
                   json={"reward_level": new_reward})

        assert self.balance(client, done) == pytest.approx(0.10)
        assert self.history(client, done) == [("Make bed", 0.10)]

    def test_renaming_a_chore_does_not_rewrite_history(self, client, done):
        client.put(f"/api/v1/chores/{done['bed']}",
                   json={"task_name": "Tidy bed"})

        assert self.history(client, done) == [("Make bed", 0.10)]

    def test_chores_done_after_the_edit_use_the_new_reward(self, client,
                                                           done):
        client.put(f"/api/v1/chores/{done['bed']}",
                   json={"reward_level": 0.20})
        client.post("/api/v1/chores/complete", json={
            "user_id": done["kid"], "chore_id": done["bed"]})

        assert self.balance(client, done) == pytest.approx(0.30)
        assert sorted(r for _, r in self.history(client, done)) == [
            0.10, 0.20]

    @patch("chores.routes.v1.user_routes.send_payout_email",
           return_value=True)
    @patch("chores.routes.v1.user_routes.requests.post")
    def test_payout_pays_what_was_earned_not_the_new_reward(
            self, post_mock, mail_mock, client, done):
        client.put(f"/api/v1/chores/{done['bed']}",
                   json={"reward_level": 5.00})

        resp = client.post(f"/api/v1/users/{done['kid']}/request_payout")

        assert resp.status_code == 200
        assert post_mock.call_args.kwargs["params"]["amount"] == \
            pytest.approx(0.10)
        details = mail_mock.call_args.kwargs["chore_details"]
        assert details == [{"name": "Make bed", "reward": 0.10}]

    def test_local_payout_pays_what_was_earned(self, client, done):
        client.put(f"/api/v1/chores/{done['bed']}",
                   json={"reward_level": 5.00})

        resp = client.post(f"/api/v1/users/{done['kid']}/payout")

        assert resp.get_json()["amount_paid"] == pytest.approx(0.10)

    def test_paid_history_keeps_its_amount_after_an_edit(self, client,
                                                         done):
        client.post(f"/api/v1/users/{done['kid']}/payout")
        client.put(f"/api/v1/chores/{done['bed']}",
                   json={"reward_level": 9.99})

        assert self.history(client, done) == [("Make bed", 0.10)]


def test_existing_completions_are_given_their_amount_on_start(
        tmp_path, monkeypatch):
    """Completions recorded before amounts were stored take the chore's
    current name and reward once, and are then independent of it."""
    import importlib
    import sqlite3
    import config
    path = tmp_path / "old.db"
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE user (id INTEGER PRIMARY KEY, name VARCHAR(100) NOT NULL,
                           email VARCHAR(120) NOT NULL UNIQUE);
        CREATE TABLE chore (id INTEGER PRIMARY KEY,
                            task_name VARCHAR(100) NOT NULL,
                            reward_level FLOAT NOT NULL);
        CREATE TABLE completion (
            id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL,
            chore_id INTEGER NOT NULL, completed_at DATETIME,
            payout_status VARCHAR(20));
        INSERT INTO user (name, email) VALUES ('Kid', 'k@home.com');
        INSERT INTO chore (task_name, reward_level) VALUES ('Make bed', 0.1);
        INSERT INTO completion (user_id, chore_id, payout_status)
            VALUES (1, 1, 'pending'), (1, 1, 'paid');
    """)
    con.commit()
    con.close()
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{path}")
    importlib.reload(config)

    old_app = create_app(config.Config)
    with old_app.app_context():
        assert [(c.task_name, c.reward) for c in Completion.query.all()] == [
            ("Make bed", 0.1)] * 2
        db.session.get(Chore, 1).reward_level = 0.5
        db.session.commit()
        db.engine.dispose()

    # A later start must not overwrite stored amounts with the new reward
    again = create_app(config.Config)
    with again.app_context():
        assert [c.reward for c in Completion.query.all()] == [0.1, 0.1]
        db.engine.dispose()

    monkeypatch.delenv("DATABASE_URL")
    importlib.reload(config)
