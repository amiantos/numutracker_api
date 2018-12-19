import requests
import json
from models import ArtistImport
from numu import db


def grab_json(uri):
    try:
        response = requests.get(uri)
    except requests.ConnectionError:
        return None
    return json.loads(response.text)


def import_artists(user, artists, import_method):
    validated_artists = []
    for artist in artists:
        try:
            validated_artists.append(str(artist))
        except ValueError:
            pass

    if len(validated_artists) == 0:
        return 0

    artists_added = 0

    for artist in validated_artists:
        found_import = ArtistImport.query.filter_by(
            user_id=user.id,
            import_name=artist).first()
        if found_import is None:
            new_import = ArtistImport(
                user_id=user.id,
                import_name=artist,
                import_mbid=None,
                import_method=import_method)
            db.session.add(new_import)
            artists_added += 1

    if artists_added > 0:
        db.session.commit()

    return artists_added
