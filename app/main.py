from flask import Flask

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

import models


app = Flask(__name__)

app.config.from_object('config.dev')
app.config.from_object('config.prod')

db = SQLAlchemy(app)
migrate = Migrate(app, db)


@app.route("/")
def hello():
    return "Numu Tracker API {}".format(app.config.get('NUMU_ENVIRONMENT'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=80)


