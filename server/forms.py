"""Sign-up & log-in forms."""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    Optional,
    NoneOf,
    NumberRange
)


class SignupForm(FlaskForm):
    """User Sign-up Form."""
    name = StringField(
        "Forum-nick",
        validators=[DataRequired(message="Ange det forum-nick du har på RCBash")]
    )
    email = StringField(
        "Epost",
        validators=[
            Length(min=6),
            Email(message="Ange en giltig epost-address"),
            DataRequired()
        ]
    )
    car_number = IntegerField(
        "Bilnummer",
        validators=[
            NumberRange(min=1, max=100, message="Du måste ange ett giltigt bilnummer")
        ]
    )
    password = PasswordField(
        "Lösenord",
        validators=[
            DataRequired(),
            Length(min=8, message="Välj ett bättre lösenord, minst 8 tecken.")
        ]
    )
    confirm = PasswordField(
        "Upprepa lösenord",
        validators=[
            DataRequired(),
            EqualTo("password", message="Lösenorden måste stämma överens.")
        ]
    )
    submit = SubmitField("Skapa konto")


class LoginForm(FlaskForm):
    """User Log-in Form."""
    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email(message="Enter a valid email.")
        ]
    )
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log In")


class NewRacedayForm(FlaskForm):
    """Form for starting a new raceday"""
    location = StringField(
        "Plats"
    )
