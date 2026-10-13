from chores.database import db


# chores/models/user.py
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120),
                      unique=True,
                      nullable=False)  # Add this
    # The Pocket Money child this user is. It is what a child's login
    # is matched on and where payouts are deposited; names are only
    # labels and may differ between the two apps.
    pm_child_id = db.Column(db.Integer, unique=True, nullable=True)
    completions = db.relationship('Completion',
                                  backref='worker',
                                  lazy=True)
