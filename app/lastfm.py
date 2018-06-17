import requests
import json

from main import db
from models import ArtistImport

from config import lastfm


def download_artists(user, username, limit=500, period='overall', page=1):
    """
    Download artists from a LastFM account into the user's library.
    Period options: overall | 7day | 1month | 3month | 6month | 12month 
    """
    uri = "http://ws.audioscrobbler.com/2.0/?method=user.gettopartists&user={}&limit={}&api_key={}&period={}&page={}&format=json".format(username, limit, lastfm.LAST_FM_API_KEY, period, page)

    try:
        uResponse = requests.get(uri)
    except requests.ConnectionError:
        return "Connection Error"
    Jresponse = uResponse.text
    data = json.loads(Jresponse)

    artists_added = 0

    for artist in data['topartists']['artist']:
        found_import = ArtistImport.query.filter_by(
            user_id=user.id,
            import_name=artist['name']).first()
        if found_import is None:
            new_import = ArtistImport(
                user_id=user.id,
                import_name=artist['name'],
                import_mbid=artist['mbid'])
            db.session.add(new_import)
            artists_added += 1

    db.session.commit()

    return {'artists_added': artists_added}
