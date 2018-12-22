"""Methods for processing content"""
from datetime import datetime, timedelta

from sqlalchemy import or_
from sqlalchemy.sql import func

import numu_mb
import repo
from lastfm import get_artist_art, get_release_art
from models import Artist, ArtistImport, Release
from numu import app as numu_app
from numu import db


def scan_artist_art(limit=100):
    date_offset = datetime.now() - timedelta(days=14)
    artists = Artist.query.filter(
        Artist.art.is_(False),
        or_(
            Artist.date_art_check < date_offset,
            Artist.date_art_check.is_(None)
        )
    ).order_by(Artist.date_art_check.asc().nullsfirst()).limit(limit).all()

    for artist in artists:
        numu_app.logger.info(
            "Checking art for artist {}, last check: {}".format(
                artist.name, artist.date_art_check))
        art_success = get_artist_art(artist)
        if art_success:
            artist.art = True
        artist.date_art_check = datetime.now()
        db.session.add(artist)
        db.session.commit()


def scan_release_art(limit=100):
    date_offset = datetime.now() - timedelta(days=14)
    releases = Release.query.filter(
        Release.art.is_(False),
        or_(
            Release.date_art_check < date_offset,
            Release.date_art_check.is_(None)
        )
    ).order_by(Release.date_art_check.asc().nullsfirst()).limit(limit).all()

    for release in releases:
        numu_app.logger.info(
            "Checking art for release {} - {}, last check: {}".format(
                release.artist_names, release.title, release.date_art_check))
        art_success = get_release_art(release)
        if art_success:
            release.art = True
        release.date_art_check = datetime.now()
        db.session.add(release)
        db.session.commit()


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
            ArtistImport.date_added.asc()
        ).limit(limit).all()

    for artist_import in artist_imports:
        found_artist = None
        numu_app.logger.info("Checking {} {}".format(
            artist_import.user_id,
            artist_import.import_name))

        if artist_import.import_method == 'V2':
            numu_app.logger.info("Searching by MBID (import from V2)")
            found_artist = repo.get_numu_artist_by_mbid(
                artist_import.import_mbid)

        if found_artist is None:
            numu_app.logger.info("Searching locally by name...")
            found_artist = repo.get_numu_artist_by_name(
                artist_import.import_name)

        if found_artist is None and check_musicbrainz:
            numu_app.logger.info("Searching MusicBrainz...")
            found_artist = numu_mb.add_numu_artist_from_mb(
                artist_name=artist_import.import_name,
                artist_mbid=artist_import.import_mbid
            )
            # Add releases
            if found_artist:
                numu_mb.add_numu_releases_from_mb(found_artist)

        if found_artist is not None:
            numu_app.logger.info("Found artist!")
            artist_import.found_mbid = found_artist.mbid
            user_artist = numu_mb.create_or_update_user_artist(
                artist_import.user_id,
                found_artist,
                artist_import.import_method)
            numu_mb.create_or_update_user_releases(user_artist, False)
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
