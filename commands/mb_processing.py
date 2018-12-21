from numu import app as numu_app
from numu_mb import update_numu_artist_from_mb
from models import Artist
from datetime import datetime, timedelta
from sqlalchemy import or_
import time
import simpleflock
#from processing import scan_artist_art, scan_release_art


@numu_app.cli.command()
def mb_processing():
    try:
        with simpleflock.SimpleFlock("mb-processing.lock", timeout=1):
            run_command()
    except BlockingIOError:
        numu_app.logger.error("Unable to achieve lock.")


def run_command():
    """This command handles the periodic querying of MusicBrainz for new data."""
    date_offset = datetime.now() - timedelta(days=14)
    limit = 200
    numu_app.logger.info("Starting MB process...")
    start = time.time()

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
    numu_app.logger.info("MB Process completed, time: {} minutes".format((end - start)/60))
