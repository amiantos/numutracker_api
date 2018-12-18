from flask import request, g

from numu import bcrypt, auth, app as numu_app
import lastfm
import response
import repo

from . import app


@app.route('/user', methods=['POST'])
def new_user():
    email = request.json.get('email')
    password = request.json.get('password')
    icloud = request.json.get('icloud')
    if (email is None or password is None) and icloud is None:
        return response.error("Email not provided.")

    if icloud and repo.get_user_by_icloud(icloud):
        return response.error("User already exists with that iCloud ID.")

    if email and repo.get_user_by_email(email):
        return response.error("User already exists with that email.")

    user = repo.insert_user(email, icloud, password)
    if user:
        return response.success("New user created: {}".format(user.id))
    else:
        return response.error("An unknown error occurred when creating the account.")


@app.route('/user')
@auth.login_required
def get_user():
    return response.success({'user': {'email': g.user.email, 'icloud': g.user.icloud}})


@app.route('/user/import/lastfm', methods=['POST'])
@auth.login_required
def import_lastfm_artists():
    """
    Import artists from Last.FM
    Arguments:
    - username: last.FM username to import artists from
    - period: ['7day', '1month', '3month', '6month', '12month', 'overall']
    - (optional) limit: maximum 500, default 500
    """
    user = g.user
    username = request.json.get('username')
    period = request.json.get('period')
    limit = request.json.get('limit')
    if username is None or period not in [
        '7day',
        '1month',
        '3month',
        '6month',
        '12month',
        'overall'
    ]:
        return response.error("Username empty or period is incorrect.")

    if limit is None or limit > 500:
        limit = 500

    result = lastfm.download_artists(user, username, limit, period)

    # backend.process_imported_artists.delay(False)

    return response.success("{} new artists imported".format(result))
