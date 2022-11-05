"""Database models."""
from typing import List, Tuple
from pathlib import Path

from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .racelogic.raceday import RESULT_FOLDER_PATH

import os
import datetime

PEPPER = os.environ["DB_PEPPER"]

ADMIN_NAME = "Admin"
RACER_NAME = "Racer"


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
        unique=True
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

    roles = db.relationship("Role", secondary="user_roles")

    def set_password(self, password):
        """Create hashed password."""
        self.password = generate_password_hash(
            self._pollute(password),
            method='sha512'
        )

    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password, self._pollute(password))

    @staticmethod
    def _pollute(password):
        return password + PEPPER

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(
        db.Integer(),
        primary_key=True
    )
    name = db.Column(
        db.String(50),
        unique=True
    )


class UserRoles(db.Model):
    __tablename__ = "user_roles"

    id = db.Column(
        db.Integer(),
        primary_key=True
    )
    user_id = db.Column(
        db.Integer(), db.ForeignKey("users.id", ondelete="CASCADE")
    )
    role_id = db.Column(
        db.Integer(), db.ForeignKey("roles.id", ondelete="CASCADE")
    )


class Race(db.Model):
    __tablename__ = "races"

    id = db.Column(
        db.Integer(),
        primary_key=True
    )

    year = db.Column(
        db.Integer(),
    )

    date = db.Column(
        db.Date(),
        unique=True
    )

    filename = db.Column(
        db.String(50),
        unique=True
    )


def get_races(season=None) -> List[Tuple[int, datetime.date, Path]]:
    races = db.session.query(Race) \
        if season is None else db.session.query(Race).filter_by(year=season)
    return [
        (race.year, race.date, RESULT_FOLDER_PATH / (race.filename + ".json"))
        for race in races
    ]


def create_past_seasons_if_necessary():
    seasons = [
        (2022, ["220430", "220528", "220702", "220806", "220903"])
    ]
    if db.session.query(Race.id).first() is None:
        for year, filenames in seasons:
            for filename in filenames:
                year = int("20" + filename[0:2])
                month = int(filename[2:4])
                day = int(filename[4:6])

                date = datetime.date(year, month, day)
                race = Race(year=year, date=date, filename=filename)
                db.session.add(race)
        db.session.commit()


def create_roles_if_necessary():
    if db.session.query(Role.id).filter_by(name=RACER_NAME).first() is None:
        admin = Role(name=ADMIN_NAME)
        racer = Role(name=RACER_NAME)
        db.session.add(admin)
        db.session.add(racer)
        db.session.commit()
