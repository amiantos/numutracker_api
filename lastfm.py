from utils import grab_json
from urllib.parse import quote_plus
from utils import put_image_from_url
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


def get_artist_art(artist):
    data = grab_json("http://ws.audioscrobbler.com/2.0/?method=artist.getinfo&artist={}&api_key={}&format=json".format(quote_plus(artist.name), app.config.get('LAST_FM_API_KEY')))

    images = data.get('artist', {}).get('image')
    if images:
        thumb_url = images[1]['#text']
        full_url = images[2]['#text']
        large_url = images[3]['#text']

        if thumb_url and full_url and large_url:
            image_name = artist.mbid + ".png"
            try:
                put_image_from_url(thumb_url, "artist/thumb/" + image_name)
                put_image_from_url(full_url, "artist/full/" + image_name)
                put_image_from_url(large_url, "artist/large/" + image_name)
                return True
            except Exception as e:
                app.logger.error("Put artist image failed: {}".format(e))
                return False

    return False


def get_release_art(release):
    data = grab_json("http://ws.audioscrobbler.com/2.0/?method=album.getinfo&artist={}&album={}&api_key={}&format=json".format(quote_plus(release.artist_names), quote_plus(release.title), app.config.get('LAST_FM_API_KEY')))

    images = data.get('album', {}).get('image')
    if images:
        thumb_url = images[1]['#text']
        full_url = images[2]['#text']
        large_url = images[3]['#text']

        if thumb_url and full_url and large_url:
            image_name = release.mbid + ".png"
            try:
                put_image_from_url(thumb_url, "release/thumb/" + image_name)
                put_image_from_url(full_url, "release/full/" + image_name)
                put_image_from_url(large_url, "release/large/" + image_name)
                return True
            except Exception as e:
                app.logger.error("Put release image failed: {}".format(e))
                return False

    return False
