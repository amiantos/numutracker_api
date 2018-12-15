import response
import db

from flask import g, jsonify, request

from app import bcrypt, app as numu_app
from app import auth

from . import app


@auth.verify_password
def verify_password(email_or_token, password):
    g.user = None
    # first try to authenticate by token
    numu_app.logger.info("Got {} - {}".format(email_or_token, password))
    if password == 'icloud':
        user = db.get_user_by_icloud(email_or_token)
        if user:
            g.user = user
            return True
    else:
        user = db.get_user_by_email(email_or_token)
        if user and bcrypt.check_password_hash(user.password, password):
            g.user = user
            return True

    return False


@app.route('/user', methods=['POST'])
def new_user():
    email = request.json.get('email')
    password = request.json.get('password')
    icloud = request.json.get('icloud')
    if (email is None or password is None) and icloud is None:
        return response.error("Email not provided.")

    if icloud and db.get_user_by_icloud(icloud):
        return response.error("User already exists with that iCloud ID.")

    if email and db.get_user_by_email(email):
        return response.error("User already exists with that email.")

    user = db.insert_user(email, icloud, password)
    if user:
        return response.success("New user created: {}".format(user.uuid))
    else:
        return response.error("An unknown error occurred when creating the account.")


@app.route('/user')
@auth.login_required
def get_user():
    return response.success({'user': {'email': g.user.email, 'icloud': g.user.icloud}})
