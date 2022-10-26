"""Database models."""
from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

import os

PEPPER = os.environ["DB_PEPPER"]


class User(UserMixin, db.Model):
    """User account model."""

    __tablename__ = "users"
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    name = db.Column(
        db.String(100),
        nullable=False,
        unique=False
    )
    email = db.Column(
        db.String(40),
        unique=True,
        nullable=False
    )
    password = db.Column(
        db.String(200),
        primary_key=False,
        unique=False,
        nullable=False
    )
    created_on = db.Column(
        db.DateTime,
        index=False,
        unique=False,
        nullable=True
    )
    last_login = db.Column(
        db.DateTime,
        index=False,
        unique=False,
        nullable=True
    )

    def set_password(self, password):
        """Create hashed password."""
        self.password = generate_password_hash(
            self._pollute(password),
            method='sha512'
        )

    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password, self.pollute(password))

    @staticmethod
    def _pollute(password):
        return password + PEPPER

    def __repr__(self):
        return '<User {}>'.format(self.username)
