from flask import abort, request, jsonify, g, url_for

from models import NumuUser
from main import db
from main import auth
from . import app


@auth.verify_password
def verify_password(email_or_token, password):
    # first try to authenticate by token
    user = NumuUser.verify_auth_token(email_or_token)
    if not user:
        # try to authenticate with username/password
        user = NumuUser.query.filter_by(email=email_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


@app.route('/user', methods=['POST'])
def new_user():
    email = request.json.get('email')
    password = request.json.get('password')
    if email is None or password is None:
        abort(400)   # missing arguments
    if NumuUser.query.filter_by(email=email).first() is not None:
        abort(400)  # existing user
    user = NumuUser(email=email)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'email': user.email}), 201, {'Location': url_for('apiv3.get_user', id=user.id, _external=True)}


@app.route('/user/<int:id>')
def get_user(id):
    user = NumuUser.query.get(id)
    if not user:
        abort(400)
    return jsonify({'email': user.email})


@app.route('/user/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token(600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})
