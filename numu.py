from flask import Flask

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


app = Flask(__name__)

app.config.from_object("config.Config")

db = SQLAlchemy(app)
import models
migrate = Migrate(app, db)


@app.route('/')
def hello_world():
    return 'Numu Tracker API'
