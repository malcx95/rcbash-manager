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
        nullable=False,
    )

    location = db.Column(
        db.String(50),
        nullable=False,
    )

    date = db.Column(
        db.Date(),
        unique=True,
        nullable=False,
    )

    filename = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
    )


def get_all_season_years() -> List[int]:
    years = [y[0] for y in db.session.query(Race.year).distinct()]
    return sorted(years, reverse=True)


def get_latest_season() -> int:
    return get_all_season_years()[0]


def get_latest_date(season: int) -> str:
    date, = db.session.query(Race.date).filter_by(year=season).order_by(Race.date.desc()).first()
    return date.strftime("%Y-%m-%d")


def get_race_dates_filenames_and_locations(season: int) -> Tuple[List[str], List[Path], List[str]]:
    races = db.session.query(Race).filter_by(year=season).order_by(Race.date.desc())
    # this is the correct type no matter what they say
    return zip(*[
        (race.date.strftime("%Y-%m-%d"), RESULT_FOLDER_PATH / (race.filename + ".json"), race.location)
        for race in races
    ])


def create_past_seasons_if_necessary():
    seasons = [
        (2022, [("220430", "Sandhem"),
                ("220528", "Linköping"),
                ("220702", "Nyköping"),
                ("220806", "Slottsbron"),
                ("220903", "Norrköping")])
    ]
    if db.session.query(Race.id).first() is None:
        for year, filenames in seasons:
            for filename, location in filenames:
                year = int("20" + filename[0:2])
                month = int(filename[2:4])
                day = int(filename[4:6])

                date = datetime.date(year, month, day)
                race = Race(year=year, date=date, filename=filename, location=location)
                db.session.add(race)
        db.session.commit()


def create_roles_if_necessary():
    if db.session.query(Role.id).filter_by(name=RACER_NAME).first() is None:
        admin = Role(name=ADMIN_NAME)
        racer = Role(name=RACER_NAME)
        db.session.add(admin)
        db.session.add(racer)
        db.session.commit()


def is_user_admin(user):
    return ADMIN_NAME in (r.name for r in user.roles)
