import time
from datetime import datetime, timedelta

from sqlalchemy import or_

import simpleflock

# from backend.import_processing import scan_imported_artists
from backend.user_artists import ImportProcessor
from backend.models import Artist, Release
from numu import app as numu_app
from backend.artists import ArtistProcessor
from backend.releases import ReleaseProcessor


@numu_app.cli.command()
def mb_processing():
    """Handle all processing tasks related to musicbrainz."""
    try:
        with simpleflock.SimpleFlock("mb-processing.lock", timeout=1):
            run_command()
    except BlockingIOError:
        numu_app.logger.info("Unable to achieve lock.")


def run_command():
    date_offset = datetime.now() - timedelta(days=3)
    limit = 200
    numu_app.logger.info("Starting MB process...")

    # Scan user imports
    ImportProcessor().import_user_artists(check_musicbrainz=True)

    # Scan artists
    artists = (
        Artist.query.filter(
            or_(Artist.date_checked < date_offset, Artist.date_checked.is_(None))
        )
        .order_by(Artist.date_checked.asc().nullsfirst())
        .limit(limit)
        .all()
    )

    for artist in artists:
        numu_app.logger.info("Updating Artist: {}".format(artist))
        updated_artist = ArtistProcessor().update_artist(artist)
        numu_app.logger.info("Updated Artist: {}".format(updated_artist))
        if updated_artist:
            releases_added = ReleaseProcessor().add_releases(updated_artist)
            numu_app.logger.info("Added Releases: {}".format(releases_added))

    # Scan releases
    releases = (
        Release.query.filter(Release.date_checked < date_offset)
        .order_by(Release.date_checked.asc())
        .limit(limit)
        .all()
    )

    for release in releases:
        numu_app.logger.info("Updating Release: {}".format(release))
        updated_release = ReleaseProcessor().update_release(release)
        numu_app.logger.info("Updated Release: {}".format(updated_release))
