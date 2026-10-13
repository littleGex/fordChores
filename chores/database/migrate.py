"""
There is no migration tool here: db.create_all() makes missing tables
but never alters existing ones. This adds columns introduced after a
database was first created. Every step is safe to run on each start.
"""
from sqlalchemy import inspect, text

from chores.database import db


def ensure_schema():
    columns = {c["name"] for c in inspect(db.engine).get_columns("user")}
    if "pm_child_id" not in columns:
        with db.engine.begin() as conn:
            conn.execute(text(
                'ALTER TABLE "user" ADD COLUMN pm_child_id INTEGER'))
            conn.execute(text(
                'CREATE UNIQUE INDEX uq_user_pm_child_id '
                'ON "user" (pm_child_id)'))
