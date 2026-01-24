from chores.database import db


class Chore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(100), nullable=False)
    reward_level = db.Column(db.Float, nullable=False)
