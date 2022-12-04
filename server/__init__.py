"""Initialize app."""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object("config.Config")

    # Initialize Plugins
    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        from . import server
        from . import auth
        from . import models

        # Register Blueprints
        app.register_blueprint(server.main_bp)
        app.register_blueprint(auth.auth_bp)

        # Create db Models
        db.create_all()

        models.create_roles_if_necessary()
        models.create_past_seasons_if_necessary()
        models.create_drivers_if_necessary()

        return app
