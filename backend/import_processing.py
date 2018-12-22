"""Import artist data from other services or apps."""
from datetime import datetime, timedelta

from sqlalchemy import or_
from sqlalchemy.sql import func

from backend import data_processing, repo
from backend.models import ArtistImport
from backend.utils import grab_json
from numu import app as numu_app
from numu import db


def import_from_lastfm(user, username, limit=500, period='overall', page=1):
    """Download artists from a LastFM account into the user's library.

    Period options: overall | 7day | 1month | 3month | 6month | 12month"""

    data = grab_json(
        "http://ws.audioscrobbler.com/2.0/?method=user.gettopartists"
        + "&user={}&limit={}&api_key={}&period={}&page={}&format=json".format(
            username,
            limit,
            numu_app.config.get('LAST_FM_API_KEY'),
            period,
            page))

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


def scan_imported_artists(check_musicbrainz=True, user_id=None):
    date_filter = datetime.now() - timedelta(days=14)
    limit = 1000
    if check_musicbrainz:
        limit = 100

    if user_id:
        artist_imports = ArtistImport.query.filter(
            ArtistImport.user_id == user_id,
            ArtistImport.found_mbid.is_(None),
            ArtistImport.date_checked.is_(None)
        ).all()
    else:
        artist_imports = ArtistImport.query.filter(
            ArtistImport.found_mbid.is_(None),
            or_(ArtistImport.date_checked < date_filter,
                ArtistImport.date_checked.is_(None))
        ).order_by(
            ArtistImport.date_checked.asc().nullsfirst(),
            ArtistImport.date_added.desc()
        ).limit(limit).all()

    for artist_import in artist_imports:
        found_artist = None
        numu_app.logger.info("Checking {} {}".format(
            artist_import.user_id,
            artist_import.import_name))

        if found_artist is None:
            numu_app.logger.info("Searching by MBID")
            found_artist = repo.get_numu_artist_by_mbid(
                artist_import.import_mbid)

        if found_artist is None:
            numu_app.logger.info("Searching locally by name...")
            found_artist = repo.get_numu_artist_by_name(
                artist_import.import_name)

        if found_artist is None and check_musicbrainz:
            numu_app.logger.info("Searching MusicBrainz...")
            found_artist = data_processing.add_numu_artist_from_mb(
                artist_name=artist_import.import_name,
                artist_mbid=artist_import.import_mbid
            )
            # Add releases
            if found_artist:
                data_processing.add_numu_releases_from_mb(found_artist)

        if found_artist is not None:
            numu_app.logger.info("Found artist!")
            artist_import.found_mbid = found_artist.mbid
            user_artist = data_processing.create_or_update_user_artist(
                artist_import.user_id,
                found_artist,
                artist_import.import_method)
            data_processing.create_or_update_user_releases(user_artist, False)
        else:
            numu_app.logger.info("Did not find artist.")
            if check_musicbrainz:
                artist_import.date_checked = func.now()

        db.session.add(artist_import)
        db.session.commit()


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
