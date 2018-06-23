import logging

from flask import Flask, make_response, jsonify

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_httpauth import HTTPBasicAuth

from celery import Celery
from config import celery as celeryconfig


app = Flask(__name__)

app.config.from_envvar('NUMU_CONFIG')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
auth = HTTPBasicAuth()


def make_celery(app):
    celery = Celery(app.import_name)
    celery.config_from_object(celeryconfig)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


celery = make_celery(app)


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


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 403)


@app.route("/")
def index():
    return "Numu Tracker API {}".format(app.config.get('NUMU_ENVIRONMENT'))


from apiv3 import app as api_v3
app.register_blueprint(api_v3, url_prefix='/v3')

from commands import app as commands
app.register_blueprint(commands)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=80)
