from chores.database import db
from datetime import datetime


class Completion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    chore_id = db.Column(db.Integer, db.ForeignKey('chore.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    payout_status = db.Column(db.String(20), default='pending')

    # What the chore was called and worth when it was done. Balances,
    # payouts and history use these, so editing or retiring a chore
    # later never changes what has already been earned or paid.
    task_name = db.Column(db.String(100), nullable=True)
    reward = db.Column(db.Float, nullable=True)

    # Relationship to get chore details easily
    chore = db.relationship('Chore')

    @property
    def earned(self):
        # Rows without a stored amount fall back to the chore's current
        # one (only possible for rows the start-up backfill couldn't fill)
        return self.reward if self.reward is not None \
            else self.chore.reward_level

    @property
    def task(self):
        return self.task_name or self.chore.task_name
