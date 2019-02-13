from backend import utils
from backend.models import Lock, User
from backend.repo import Repo
from backend.user_artists import ImportProcessor
from backend.releases import ReleaseProcessor
from numu import app as numu_app


repo = Repo()
import_processor = ImportProcessor(repo=repo)
release_processor = ReleaseProcessor(repo=repo)


@numu_app.cli.command()
def import_user_data():
    """Import user data from V2 automatically."""
    process_name = "import_user_data"
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
    limit = 100
    users = (
        User.query.order_by(User.date_v2_import.asc().nullsfirst()).limit(limit).all()
    )
    for user in users:
        username = user.email if user.email else user.icloud

        data = utils.grab_json(
            "https://www.numutracker.com/v2/json2.php?importv2={}&key={}".format(
                username, numu_app.config.get("NUMU_V2_API_KEY")
            )
        )

        filters = data.get("filters")
        if filters:
            user.album = bool(filters["album"])
            user.ep = bool(filters["ep"])
            user.single = bool(filters["single"])
            user.live = bool(filters["live"])
            user.soundtrack = bool(filters["soundtrack"])
            user.remix = bool(filters["remix"])
            user.other = bool(filters["other"])
            repo.save(user)
            repo.commit()

        artists = data.get("artists")
        if artists:
            imported = import_processor.save_imports(user.id, artists, "v2")
            print("Imported {} artists from V2...".format(imported))

        listens = data.get("listens", [])
        releases_added = 0
        for listen in listens:
            release_mbid = listen.get("mbid")
            release = repo.get_release_by_mbid(release_mbid)

            if release:
                user_release, notify = release_processor.add_user_release(
                    release, user_id=user.id, follow_method="v2"
                )
                user_release.listened = True
                user_release.date_listened = listen.get("listen_date")
                repo.save(user_release)
                if notify:
                    releases_added += 1
        repo.commit()
        print("Listens imported: {}".format(releases_added))

        user.date_v2_import = utils.now()
        repo.save(user)
        repo.commit()
