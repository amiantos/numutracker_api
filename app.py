import logging
import os
from flask import Flask
from flask_httpauth import HTTPBasicAuth


app = Flask(__name__)

auth = HTTPBasicAuth()


@app.route('/')
def hello_world():
    return 'Numu Tracker API - {}'.format(os.environ.get('environment'))


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


from apiv3 import app as api_v3
app.register_blueprint(api_v3, url_prefix='/v3')