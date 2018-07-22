from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, HiddenField)
from wtforms.validators import (DataRequired, ValidationError,
                                Email, Length, EqualTo)

from models import User


def username_exists(form, field):
    if User.select().where(User.username == field.data).exists():
        raise ValidationError('User with that username already exists.')


def email_exists(form, field):
    if User.select().where(User.email == field.data).exists():
        raise ValidationError('User with that email already exists.')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), username_exists])
    email = StringField('Email', validators=[DataRequired(), Email(), email_exists])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8),
        EqualTo('verify_password', message='Both passwords must match')
    ])
    verify_password = PasswordField('Verify Password', validators=[DataRequired()])
