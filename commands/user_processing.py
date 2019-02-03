from numu import app as numu_app
from backend.user_artists import ImportProcessor
import simpleflock


@numu_app.cli.command()
def user_processing():
    try:
        with simpleflock.SimpleFlock("user-processing.lock", timeout=1):
            run_command()
    except BlockingIOError:
        numu_app.logger.error("Unable to achieve lock.")


def run_command():
    """This command ensures that all users have the most updated releases."""

    # Scan artist imports
    ImportProcessor().import_user_artists(check_musicbrainz=False)
