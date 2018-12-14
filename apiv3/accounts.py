import uuid

import boto3
from flask import jsonify, request

from app import app as numu_app
from app import auth, bcrypt

from . import app

USERS_TABLE = numu_app.config.get('USERS_TABLE')
dyanmodb = boto3.client('dynamodb')


@auth.verify_password
def verify_password(email_or_token, password):
    # first try to authenticate by token
    numu_app.logger.info("Got {} - {}".format(email_or_token, password))
    return True


@app.route('/user', methods=['POST'])
def new_user():
    email = request.json.get('email')
    password = request.json.get('password')
    icloud = request.json.get('icloud')
    if (email is None or password is None) and icloud is None:
        return jsonify({'error': 'Email or password not provided.'}), 400
    # Check for existing user

    # Create new user record
    user_uuid = uuid.uuid4().hex
    user_item = {
        'uuid': {'S': user_uuid}
    }
    if password:
        hashed_password = bcrypt.generate_password_hash(password)
        user_item['password'] = {'B': hashed_password}
    if email:
        user_item['email'] = {'S': email}
    if icloud:
        user_item['icloud'] = {'S': icloud}

    resp = dyanmodb.put_item(
        TableName=USERS_TABLE,
        Item=user_item)

    return jsonify({'uuid': user_uuid}), 201


@app.route('/user')
@auth.login_required
def get_user():
    numu_app.logger.info("Got Self.")
    return jsonify({'email': 'Moo'})
