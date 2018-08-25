import redis
from celery.schedules import crontab
from main import celery
from main import app as numu_app
import backend


REDIS_CLIENT = redis.Redis(host='redis', password='numu_tracker')

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):

    sender.add_periodic_task(
        30,
        run_updates.s(),
        name='Updates'
    )

    # Executes every morning at 8:00 AM PST.
    """sender.add_periodic_task(
        crontab(minute=0, hour=15),
        test.s('Run Notifications'),
        name='Notifications'
    )"""


@celery.task
def run_updates():
    numu_app.logger.info("Processing Imported Artists...")
    backend.process_imported_artists()
    numu_app.logger.info("Completed: Imported Artists.")

    numu_app.logger.info("Updating Artists")
    backend.update_artists()
    numu_app.logger.info("Completed: Updating Artists.")

    return True
