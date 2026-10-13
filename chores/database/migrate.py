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

    columns = {c["name"] for c in inspect(db.engine).get_columns("chore")}
    if "archived" not in columns:
        with db.engine.begin() as conn:
            conn.execute(text(
                'ALTER TABLE chore ADD COLUMN archived BOOLEAN '
                'NOT NULL DEFAULT FALSE'))

    columns = {c["name"]
               for c in inspect(db.engine).get_columns("completion")}
    with db.engine.begin() as conn:
        if "task_name" not in columns:
            conn.execute(text(
                'ALTER TABLE completion ADD COLUMN task_name VARCHAR(100)'))
        if "reward" not in columns:
            conn.execute(text(
                'ALTER TABLE completion ADD COLUMN reward FLOAT'))
        # Completions recorded before the amount was stored take the
        # chore's current name and reward: the best record there is.
        # Only touches rows that have none, so it is safe on every start.
        conn.execute(text(
            'UPDATE completion SET '
            'task_name = (SELECT task_name FROM chore '
            '             WHERE chore.id = completion.chore_id), '
            'reward = (SELECT reward_level FROM chore '
            '          WHERE chore.id = completion.chore_id) '
            'WHERE reward IS NULL OR task_name IS NULL'))
