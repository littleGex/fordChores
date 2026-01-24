from chores import create_app
from chores.database import db
from chores.models.user import User
from chores.models.chore import Chore


def seed_data():
    app = create_app()
    with app.app_context():
        # 1. Create tables based on models
        db.create_all()

        # 2. Check if data already exists to avoid duplicates
        if User.query.first():
            print("Database already seeded.")
            return

        # 3. Add Users
        admin = User(name="Admin Parent", email="parent@home.com")
        child = User(name="Alex", email="alex@home.com")

        # 4. Add Chores
        dishes = Chore(task_name="Dishes", reward_level=2.00)
        mow = Chore(task_name="Mow Lawn", reward_level=15.00)
        trash = Chore(task_name="Take out Trash", reward_level=1.00)

        # 5. Save to Database
        db.session.add_all([admin, child, dishes, mow, trash])
        db.session.commit()
        print("Database successfully seeded with users and chores!")


if __name__ == "__main__":
    seed_data()
