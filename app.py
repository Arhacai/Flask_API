from flask import Flask, g, jsonify, render_template, flash, redirect, url_for
from flask_argon2 import check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_ipaddr
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)

import config
import forms
import models
from auth import auth
from resources.todos import todos_api
from resources.users import users_api

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

app.register_blueprint(users_api, url_prefix='/api/v1')
app.register_blueprint(todos_api, url_prefix='/api/v1')

limiter = Limiter(app, default_limits=[config.DEFAULT_RATE], key_func=get_ipaddr)
limiter.limit("40/day")(users_api)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(userid):
    try:
        return models.User.get(models.User.id == userid)
    except models.DoesNotExist:
        return None


@app.before_request
def before_request():
    """Connect to the database before each request."""
    g.db = models.DATABASE
    try:
        g.db.connect()
    except:
        g.db.close()
        g.db.connect()
    else:
        g.user = current_user


@app.after_request
def after_request(response):
    """Close the database connection after each requests."""
    g.db.close()
    return response


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = forms.RegisterForm()
    if form.validate_on_submit():
        flash("You've been succesfully registered!", 'success')
        user = models.User.create_user(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data
        )
        login_user(user)
        return redirect(url_for('my_todos'))
    return render_template('register.html', form=form)


@app.route('/login', methods=('GET', 'POST'))
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        try:
            user = models.User.get(models.User.email == form.email.data)
        except models.DoesNotExist:
            flash("Your email or password doesn't match!", "error")
        else:
            if check_password_hash(user.password, form.password.data):
                g.user = user
                login_user(user)
                flash("You've been logged in!", "success")
                return redirect(url_for('my_todos'))
            else:
                flash("Your email or password doesn't match!", "error")
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You've been logged out! Come back soon!", "success")
    return redirect(url_for('login'))


@app.route('/', methods=['GET', 'POST'])
@login_required
def my_todos():
    return render_template('index.html')


@app.route('/api/v1/users/token', methods=['GET'])
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    return jsonify({'token': token.decode('ascii')})


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


def initialize_todos():
    try:
        testuser = models.User.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password',
            verify_password='password'
        )
        otheruser = models.User.create_user(
            username='otheruser',
            email='otheruser@example.com',
            password='password',
            verify_password='password'
        )
        models.Todo.create(name='clean the house', created_by=testuser)
        models.Todo.create(name='water the dog', created_by=otheruser)
        models.Todo.create(name='feed the lawn', created_by=testuser)
        models.Todo.create(name='pay dem bills', created_by=otheruser)
        models.Todo.create(name='run', created_by=testuser)
        models.Todo.create(name='swim', created_by=otheruser)
    except:
        pass


if __name__ == '__main__':
    models.initialize()
    initialize_todos()
    app.run(debug=config.DEBUG, host=config.HOST, port=config.PORT)
