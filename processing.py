"""Methods for processing content"""
from datetime import datetime, timedelta
from models import Artist, Release
from lastfm import get_artist_art, get_release_art
from sqlalchemy import or_
from numu import app as numu_app, db


def scan_artist_art(limit=100):
    date_offset = datetime.now() - timedelta(days=14)
    artists = Artist.query.filter(
        Artist.art.is_(False),
        or_(
            Artist.date_art_check < date_offset,
            Artist.date_art_check.is_(None)
        )
    ).order_by(Artist.date_art_check.desc()).limit(limit).all()

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
    ).order_by(Release.date_art_check.desc()).limit(limit).all()

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
