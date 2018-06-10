from flask import Flask, make_response, jsonify

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_httpauth import HTTPBasicAuth


app = Flask(__name__)

app.config.from_envvar('NUMU_CONFIG')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
auth = HTTPBasicAuth()


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


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=80)
