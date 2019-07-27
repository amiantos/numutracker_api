from numu import app as numu_app
from backend.images import scan_artist_art, scan_release_art
from backend.repo import Repo
from backend.models import Lock
from backend import utils


@numu_app.cli.command()
def check_art():
    """Check for artist and release art, and save to storage."""
    repo = Repo()
    process_name = "check_art"
    lock = Lock.query.filter_by(process_name=process_name).first()
    if lock is None:
        lock = Lock(process_name=process_name, lock_acquired=False)
    if lock.lock_acquired is False or (
        lock.lock_acquired is True
        and lock.date_acquired < utils.now() - timedelta(hours=1)
    ):
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
    """Check for artist and release art."""
    numu_app.logger.info("Checking artist art...")
    scan_artist_art()

    numu_app.logger.info("Checking release art...")
    scan_release_art()

    numu_app.logger.info("Art check finished!")
