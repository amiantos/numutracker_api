from flask import Flask

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_httpauth import HTTPBasicAuth


app = Flask(__name__)

app.config.from_object('config.dev')
app.config.from_object('config.prod')

db = SQLAlchemy(app)
migrate = Migrate(app, db)
auth = HTTPBasicAuth()


@app.route("/")
def index():
    return "Numu Tracker API {}".format(app.config.get('NUMU_ENVIRONMENT'))


from apiv3 import app as api_v3
app.register_blueprint(api_v3, url_prefix='/v3')


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=80)
