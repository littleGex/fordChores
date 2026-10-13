"""
Logins for the chore tracker. There are no accounts here: a caller sends
the bearer token they got from the family login (the fordDbs API), and
we ask that API who it belongs to. Roles and account status are checked
there, in one place.
"""
import os
from functools import wraps

import requests
from flask import abort, g, jsonify, request

from chores.models import User

PARENT_ROLES = ("parent", "admin")
# Adults outside the household have no business here
ALLOWED_ROLES = PARENT_ROLES + ("child",)


def _whoami_url():
    return os.getenv("AUTH_ME_URL") or (
        f"{os.getenv('PM_BASE_URL')}/v1/family-photos/me")


def _fail(status, message):
    response = jsonify({"error": message})
    response.status_code = status
    abort(response)


def fetch_identity(authorization):
    """Asks the family login API who a bearer token belongs to. Returns
    (status_code, profile-or-None)."""
    res = requests.get(_whoami_url(),
                       headers={"Authorization": authorization}, timeout=5)
    return res.status_code, (res.json() if res.status_code == 200 else None)


def load_identity():
    """
    Blueprint before_request hook: every route needs a family login.
    Puts the caller's profile on flask.g.identity.
    """
    # CORS preflights carry no credentials
    if request.method == "OPTIONS":
        return

    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        _fail(401, "Not authenticated")

    try:
        status, identity = fetch_identity(header)
    except requests.exceptions.RequestException:
        _fail(503, "Login service unavailable")

    if status == 401:
        _fail(401, "Not authenticated")
    if status != 200:
        _fail(503, "Login service unavailable")
    if identity.get("role") not in ALLOWED_ROLES:
        _fail(403, "Forbidden")
    g.identity = identity


def is_parent():
    return g.identity["role"] in PARENT_ROLES


def parents_only(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not is_parent():
            _fail(403, "Parents only")
        return view(*args, **kwargs)
    return wrapper


def own_user():
    """The chore-tracker user a child's login belongs to: the one linked
    to the same Pocket Money child as their family account."""
    child_id = g.identity.get("child_id")
    if child_id is None:
        return None
    return User.query.filter_by(pm_child_id=child_id).first()


def authorize_user(user_id):
    """Parents may act for any user; a child only for themselves."""
    if is_parent():
        return
    me = own_user()
    if me is None or me.id != int(user_id):
        _fail(403, "Forbidden")
