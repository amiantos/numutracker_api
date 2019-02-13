from backend import utils
from backend.models import Lock
from backend.repo import Repo
from backend.user_artists import ImportProcessor
from numu import app as numu_app


@numu_app.cli.command()
def user_processing():
    """Perform quick check of user imports."""
    repo = Repo()
    process_name = "user_processing"
    lock = Lock.query.filter_by(process_name=process_name).first()
    if lock is None:
        lock = Lock(process_name=process_name, lock_acquired=False)
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
    ImportProcessor().import_user_artists(check_musicbrainz=False)
