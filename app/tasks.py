import redis
import time
from celery.schedules import crontab
from main import celery
from main import app as numu_app


REDIS_CLIENT = redis.Redis()


def only_one(function=None, key="", timeout=None):
    """Enforce only one celery task at a time."""

    def _dec(run_func):
        """Decorator."""

        def _caller(*args, **kwargs):
            """Caller."""
            ret_value = None
            have_lock = False
            lock = REDIS_CLIENT.lock(key, timeout=timeout)
            try:
                have_lock = lock.acquire(blocking=False)
                if have_lock:
                    ret_value = run_func(*args, **kwargs)
            finally:
                if have_lock:
                    lock.release()

            return ret_value

        return _caller

    return _dec(function) if function is not None else _dec


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):

    sender.add_periodic_task(
        5,
        test.s('Test Celery Task'),
        name='Test Tasks'
    )

    sender.add_periodic_task(
        900,
        test.s('Run Updates'),
        name='Updates'
    )

    # Executes every morning at 8:00 AM PST.
    sender.add_periodic_task(
        crontab(minute=0, hour=15),
        test.s('Run Notifications'),
        name='Notifications'
    )


@celery.task
@only_one(key="numu_task", timeout=60 * 5)
def test(arg):
    time.sleep(5)
    numu_app.logger.info("Hello")
