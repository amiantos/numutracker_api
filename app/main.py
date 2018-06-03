from flask import Flask


app = Flask(__name__)

app.config.from_object('config.dev')
app.config.from_object('config.prod')


@app.route("/")
def hello():
    return "Numu Tracker API {}".format(app.config.get('NUMU_ENVIRONMENT'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=80)
