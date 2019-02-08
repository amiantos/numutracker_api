from datetime import datetime, timedelta

from backend import utils
from backend.artists import ArtistProcessor
from backend.models import Artist, Lock, Release
from backend.releases import ReleaseProcessor
from backend.repo import Repo
from backend.user_artists import ImportProcessor
from numu import app as numu_app
from sqlalchemy import or_


@numu_app.cli.command()
def mb_processing():
    """Handle all processing tasks related to musicbrainz."""
    repo = Repo()
    process_name = "mb_processing"
    lock = Lock.query.filter_by(process_name=process_name).first()
    if lock is None:
        lock = Lock(process_name="mb_processing", lock_acquired=False)
    if lock.lock_acquired is False:
        lock.lock_acquired = True
        lock.date_acquired = utils.now()
        repo.save(lock)
        repo.commit()

        run_command()

        lock.lock_acquired = False
        repo.save(lock)
        repo.commit()
    else:
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
