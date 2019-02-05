from numu import app as numu_app
from backend.user_artists import ImportProcessor
import simpleflock


@numu_app.cli.command()
def user_processing():
    """Perform quick check of user imports."""
    try:
        with simpleflock.SimpleFlock("user-processing.lock", timeout=1):
            run_command()
    except BlockingIOError:
        numu_app.logger.info("Unable to achieve lock.")


def run_command():
    ImportProcessor().import_user_artists(check_musicbrainz=False)
