import time
from datetime import datetime, timedelta

from sqlalchemy import or_

import simpleflock
from backend.import_processing import scan_imported_artists
from backend.models import Artist
from numu import app as numu_app
from backend.data_processing import update_numu_artist_from_mb


@numu_app.cli.command()
def mb_processing():
    try:
        with simpleflock.SimpleFlock("mb-processing.lock", timeout=1):
            run_command()
    except BlockingIOError:
        numu_app.logger.error("Unable to achieve lock.")


def run_command():
    date_offset = datetime.now() - timedelta(days=14)
    limit = 200
    numu_app.logger.info("Starting MB process...")
    start = time.time()

    # Scan user imports
    scan_imported_artists(True)

    # Scan artists
    artists = Artist.query.filter(
        or_(
            Artist.date_checked < date_offset,
            Artist.date_checked.is_(None)
        )
    ).order_by(Artist.date_checked.asc().nullsfirst()).limit(limit).all()

    for artist in artists:
        current_time = time.time()
        if (current_time - start)/60 < 14:
            numu_app.logger.info("Updating Artist: {}".format(artist))
            updated_artist = update_numu_artist_from_mb(artist)
            numu_app.logger.info("Updated Artist: {}".format(updated_artist))
        else:
            numu_app.logger.error("Hit maximum execution time, aborting...")
            break

    # Scan releases

    end = time.time()
    numu_app.logger.info(
        "MB Process completed, time: {} minutes".format((end - start)/60))
