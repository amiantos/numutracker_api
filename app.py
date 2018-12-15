import logging
from os import environ

from flask import Flask
from flask_httpauth import HTTPBasicAuth

from apiv3 import app as api_v3
from flask_bcrypt import Bcrypt


app = Flask(__name__)

bcrypt = Bcrypt(app)

auth = HTTPBasicAuth()

app.config.from_object("config.%s" % environ.get('NUMU_ENV', 'development').title())


@app.route('/')
def hello_world():
    return 'Numu Tracker API - {}'.format(app.config.get('ENVIROMENT'))


@app.before_first_request
def setup_logging():
    if not app.debug:
        log_handler = logging.StreamHandler()
        log_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        log_handler.setLevel(logging.INFO)
        app.logger.addHandler(log_handler)
        app.logger.setLevel(logging.INFO)


app.register_blueprint(api_v3, url_prefix='/v3')
