import os
from flask import Flask


app = Flask(__name__)

app.config.from_object('config')
if "NUMU_SETTINGS" in os.environ:
    app.config.from_envvar('NUMU_SETTINGS')


@app.route("/")
def hello():
    return "Numu Tracker API {}".format(app.config.get('NUMU_ENVIRONMENT'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=80)
