from flask import jsonify, g

from app import auth
from app import app as numu_app
from . import app


@auth.verify_password
def verify_password(email_or_token, password):
    # first try to authenticate by token
    numu_app.logger.info("Got {} - {}".format(email_or_token, password))
    return True


"""
@app.route('/user', methods=['POST'])
def new_user():
    email = request.json.get('email')
    password = request.json.get('password')
    if email is None or password is None:
        return jsonify({'error': 'Email or password not provided.'}), 400
    if User.query.filter_by(email=email).first() is not None:
        return jsonify(
            {'error': 'A user with that email already exists.'}
        ), 400
    user = User(email=email)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'email': user.email}), 201
"""


@app.route('/user')
@auth.login_required
def get_user():
    numu_app.logger.info("Got Self.")
    return jsonify({'email': 'Moo'})
