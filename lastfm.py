from utils import grab_json

from numu import app, db
from models import ArtistImport


def download_artists(user, username, limit=500, period='overall', page=1):
    """Download artists from a LastFM account into the user's library.

    Period options: overall | 7day | 1month | 3month | 6month | 12month"""

    data = grab_json("http://ws.audioscrobbler.com/2.0/?method=user.gettopartists&user={}&limit={}&api_key={}&period={}&page={}&format=json".format(username, limit, app.config.get('LAST_FM_API_KEY'), period, page))

    artists_added = 0

    for artist in data.get('topartists').get('artist'):
        found_import = ArtistImport.query.filter_by(
            user_id=user.id,
            import_name=artist['name']).first()
        if found_import is None:
            new_import = ArtistImport(
                user_id=user.id,
                import_name=artist['name'],
                import_mbid=artist['mbid'],
                import_method='lastfm')
            db.session.add(new_import)
            artists_added += 1

    if artists_added > 0:
        db.session.commit()

    return artists_added
