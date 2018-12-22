from flask import request, g

from numu import auth, app as numu_app
import lastfm
import response
import repo
from processing import import_artists, scan_imported_artists

from . import app


@app.route('/user', methods=['POST'])
def new_user():
    email = request.json.get('email')
    password = request.json.get('password')
    icloud = request.json.get('icloud')
    if (email is None or password is None) and icloud is None:
        return response.error("Proper account credentials were not provided.")

    if icloud and repo.get_user_by_icloud(icloud):
        return response.error("Registration failed.")

    if email and repo.get_user_by_email(email):
        return response.error("Registration failed.")

    user = repo.insert_user(email, icloud, password)
    if user:
        numu_app.logger.info("New user created: {}".format(user.id))
        return response.success("New user created: {}".format(user.id))
    else:
        numu_app.logger.error("New user failed to save.")
        return response.error("An unknown error occurred when creating this account.")


@app.route('/user')
@auth.login_required
def get_user():
    return response.success({'user': {'email': g.user.email, 'icloud': g.user.icloud}})


@app.route('/user/import', methods=['POST'])
@auth.login_required
def import_artists_endpoint():
    """
    Import artists
    Arguments:
    - artists: [string]
    - import_method: ['apple', 'spotify']
    """
    user = g.user
    artists = request.json.get('artists')
    import_method = request.json.get('import_method')
    if not artists or len(artists) == 0:
        return response.error("Missing artists dictionary.")
    if not import_method:
        return response.error("Missing import_method")

    result = import_artists(user, artists, import_method)
    if result > 0:
        scan_imported_artists(False, user.id)

    return response.success({'artists_imported': result})


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

    return response.success({'artists_imported': result})
