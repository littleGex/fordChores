from chores.database import db


class Chore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(100), nullable=False)
    reward_level = db.Column(db.Float, nullable=False)
    # A chore that has been done at least once can't be deleted while
    # completions still point at it, so it is retired instead: hidden
    # from the lists, kept for the records.
    archived = db.Column(db.Boolean, nullable=False, default=False,
                         server_default=db.false())
