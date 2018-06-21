from flask import abort, request, jsonify, g, url_for

from models import User
from main import db
from main import auth
from main import app as numu_app
import lastfm as lfm
from . import app
import backend


@auth.verify_password
def verify_password(email_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(email_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(email=email_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True


@app.route('/user', methods=['POST'])
def new_user():
    email = request.json.get('email')
    password = request.json.get('password')
    if email is None or password is None:
        return jsonify({'error': 'Email or password not provided.'}), 400
    if User.query.filter_by(email=email).first() is not None:
        return jsonify({'error': 'A user with that email already exists.'}), 400
    user = User(email=email)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'email': user.email}), 201, {'Location': url_for('apiv3.get_user', id=user.id, _external=True)}


@app.route('/user')
@auth.login_required
def get_user():
    numu_app.logger.info("Got Self.")
    return jsonify({'email': g.user.email})


@app.route('/user/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token(600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})


@app.route('/user/import/lastfm', methods=['POST'])
@auth.login_required
def import_artists():
    """
    Import artists from Last.FM
    Arguments:
    - username: last.FM username to import artists from
    - period: '7day', '1month', '3month', '6month', '12month', 'overall'
    - (optional) limit: maximum 500, default 500
    """
    user = g.user
    username = request.json.get('username')
    period = request.json.get('period')
    limit = request.json.get('limit')
    if username is None or period not in ['7day', '1month', '3month', '6month', '12month', 'overall']:
        return jsonify({'error': 'Username empty or period is incorrect.'}), 400

    if limit is None or limit > 500:
        limit = 500

    result = lfm.download_artists(user, username, limit, period)

    backend.import_artists.delay(False)

    return jsonify(result), 200
