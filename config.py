import os

class Config:
    """Configuration of Flask app"""

    FLASK_ENV = os.environ["FLASK_ENV"]
    SECRET_KEY = os.environ["SECRET_KEY"]

    STATIC_FOLDER = "static"
    TEMPLATES_FOLDER = "templates"

    SQLALCHEMY_DATABASE_URI = os.environ["SQLALCHEMY_DATABASE_URI"]
