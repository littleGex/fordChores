from chores.database import db
from datetime import datetime


class Completion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    chore_id = db.Column(db.Integer, db.ForeignKey('chore.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    payout_status = db.Column(db.String(20), default='pending')

    # Relationship to get chore details easily
    chore = db.relationship('Chore')
