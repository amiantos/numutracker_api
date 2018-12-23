import logging
import response

from flask import Flask, make_response, jsonify, g

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_httpauth import HTTPBasicAuth
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)
auth = HTTPBasicAuth()

app.config.from_object("config.Config")

db = SQLAlchemy(app)

import backend.models
migrate = Migrate(app, db)



@app.before_first_request
def setup_logging():
    if not app.debug:
        log_handler = logging.StreamHandler()
        log_handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(pathname)s:%(lineno)d | %(funcName)s | %(levelname)s | %(message)s"
        ))
        log_handler.setLevel(logging.INFO)
        app.logger.addHandler(log_handler)
        app.logger.setLevel(logging.INFO)


from backend import repo


@auth.verify_password
def verify_password(username, password):
    g.user = None
    if password == 'icloud':
        user = repo.get_user_by_icloud(username)
        if user:
            g.user = user
            return True
    else:
        user = repo.get_user_by_email(username)
        if user and bcrypt.check_password_hash(user.password_hash, password):
            g.user = user
            return True

    return False


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@auth.error_handler
def unauthorized():
    return response.unauthorized()


@app.route('/')
def index():
    return 'Numu Tracker API - {}'.format(app.config['ENVIROMENT'])


from rest import app as api_v3
app.register_blueprint(api_v3, url_prefix='/v3')


from commands import app as commands
app.register_blueprint(commands)
