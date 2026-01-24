from flask import Flask
from flask_cors import CORS
from config import Config
from chores.database import db
from chores.extension import mail


def create_app(config_class=Config):
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(config_class)

    # 1. Initialize the database with this specific app
    db.init_app(app)
    mail.init_app(app)

    # 2. IMPORT MODELS HERE
    # This is crucial! If you don't import them, db.create_all() will be empty.
    from chores.models.user import User
    from chores.models.chore import Chore
    from chores.models.completion import Completion

    # 3. Register Blueprints (Versioning)
    from chores.routes.v1.chore_routes import chore_v1
    from chores.routes.v1.user_routes import user_v1

    app.register_blueprint(chore_v1)
    app.register_blueprint(user_v1)

    with app.app_context():
        # This creates the .db file and tables if they don't exist
        db.create_all()

    return app
