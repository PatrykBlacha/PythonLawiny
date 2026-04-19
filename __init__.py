import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_cors import CORS

PNG_PATH = 'static/risk_map.png'

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
default_db_uri = 'sqlite:///' + os.path.join(basedir, 'users.db')

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', default_db_uri)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tajny klucz')

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
CORS(app)