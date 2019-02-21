from sqlalchemy.sql import func

from backend.artists import ArtistProcessor
from backend import musicbrainz
from backend.models import Release, UserRelease, DeletedRelease
from backend.repo import Repo
from numu import app as numu_app
from backend import utils
from datetime import datetime


class NotFoundError(Exception):
    pass


class ReleaseProcessor:
    def __init__(self, repo=None, mbz=None):
        self.repo = repo or Repo()
        self.mbz = mbz or musicbrainz
        self.logger = numu_app.logger
        self.artist_processor = ArtistProcessor(repo=self.repo, mbz=self.mbz)

    # ------------------------------------
    # Add
    # ------------------------------------

    def add_release(self, mbid):
        release = self.repo.get_release_by_mbid(mbid)
        if release is None:
            mb_release = self.mbz.get_release(mbid)

            if mb_release.get("release") and mb_release.get("status") == 200:
                release = self._save_mb_release(mb_release["release"])

        return release

    def add_releases(self, artist):
        self.logger.info("Adding releases for {}".format(artist))
        mb_releases = self.mbz.get_artist_releases(artist.mbid)
        releases_added = []

        if mb_releases["status"] != 200:
            self.logger.info("No releases found.")
            return None

        for mb_release in mb_releases["releases"]:
            if mb_release.get("id") in releases_added:
                continue

            release = self.repo.get_release_by_mbid(mb_release.get("id"))
            if release:
                release = self._update_release(release, mb_release)
                continue

            self.logger.info("Release not found locally.")
            release = self._save_mb_release(mb_release)

            if release is not None:
                # Add release to users following this artist...
                user_artists = self.repo.get_user_artists_by_mbid(artist.mbid)
                for user_artist in user_artists:
                    self.add_user_releases(user_artist, [release], True)
                releases_added.append(release.mbid)

        artist.date_checked = func.now()
        self.repo.save(artist)
        self.repo.commit()

        self.logger.info("Added {} releases for {}".format(len(releases_added), artist))

        return len(releases_added)

    def _save_mb_release(self, mb_release):
        date_release = utils.convert_mb_release_date(
            mb_release.get("first-release-date")
        )
        if date_release is None or mb_release.get("artist-credit") is None:
            self.logger.info(
                "Release {} - {} does not qualify for inclusion".format(
                    mb_release.get("id"), mb_release.get("title")
                )
            )
            return None

        release = Release(
            mbid=mb_release.get("id"),
            title=mb_release.get("title"),
            type=utils.get_release_type(mb_release),
            date_release=date_release,
            artist_names=mb_release.get("artist-credit-phrase"),
            date_updated=func.now(),
        )
        self.logger.info("New release created: {}".format(release))

        for mb_artist in mb_release.get("artist-credit"):
            if type(mb_artist) == dict and mb_artist["artist"]:
                artist = self.artist_processor.add_artist(
                    mbid=mb_artist["artist"]["id"]
                )
                if artist and artist not in release.artists:
                    self.logger.info("Artist credit created for {}".format(artist))
                    release.artists.append(artist)

        self.repo.save(release)

        return release

    def add_user_release(self, release, user_id, follow_method="AUTOMATIC"):
        notify = False
        user_release = self.repo.get_user_release(user_id, release.mbid)
        if user_release is None:
            user_release = UserRelease(
                user_id=user_id, mbid=release.mbid, follow_method=follow_method
            )
            notify = True
            self.repo.save(user_release)
            self.logger.info("New user release created {}".format(user_release))

        return user_release, notify

    def add_user_releases(self, user_artist, releases, notifications):
        for release in releases:
            user_release, notify = self.add_user_release(
                release, user_id=user_artist.user_id
            )
            if notifications and notify:
                # TODO: Create notification
                pass

    # ------------------------------------
    # Update
    # ------------------------------------

    def update_release(self, release):
        mb_result = self.mbz.get_release(release.mbid)

        if mb_result.get("status") == 404:
            self.logger.error("Release no longer found in MB: {}".format(release))
            return self.delete_release(release, "removed from musicbrainz")

        if mb_result.get("status") == 200:
            mb_release = mb_result.get("release")
            release = self._update_release(release, mb_release)

        return release

    def _update_release(self, release, mb_release):
        date_release = utils.convert_mb_release_date(
            mb_release.get("first-release-date")
        )
        if date_release is None or mb_release.get("artist-credit") is None:
            self.logger.error(
                "Release {} - {} no longer qualifies for inclusion".format(
                    mb_release.get("id"), mb_release.get("title")
                )
            )
            return self.delete_release(release, "no longer qualifies")

        current_date_release = ""
        try:
            current_date_release = release.date_release.strftime("%Y-%m-%d")
        except AttributeError:
            current_date_release = release.date_release

        has_release_changed = (
            release.title != mb_release.get("title")
            or release.type != utils.get_release_type(mb_release)
            or current_date_release != date_release
            or release.artist_names != mb_release.get("artist-credit-phrase")
        )

        if has_release_changed:
            release.title = mb_release.get("title")
            release.type = utils.get_release_type(mb_release)
            release.date_release = date_release
            release.artist_names = mb_release.get("artist-credit-phrase")
            release.date_updated = func.now()

            for mb_artist in mb_release.get("artist-credit"):
                if type(mb_artist) == dict and mb_artist["artist"]:
                    artist = self.artist_processor.add_artist(
                        mbid=mb_artist["artist"]["id"]
                    )
                    if artist and artist not in release.artists:
                        self.logger.info("Artist credit created for {}".format(artist))
                        release.artists.append(artist)

        release.date_checked = func.now()
        self.repo.save(release)

        return release

    def update_user_releases(self, artist, user_artist=None, notifications=True):
        releases = self.repo.get_releases_by_artist_mbid(artist.mbid)
        if user_artist:
            self.add_user_releases(user_artist, releases, notifications)
        else:
            user_artists = self.repo.get_user_artists_by_mbid(artist.mbid)
            for user_artist in user_artists:
                self.add_user_releases(user_artist, releases, notifications)
        self.repo.commit()

    # ------------------------------------
    # Delete
    # ------------------------------------

    def delete_release(self, release, reason=None):
        deleted_release = DeletedRelease(mbid=release.mbid, meta=reason)
        self.repo.save(deleted_release)
        self.repo.delete(release)
        self.repo.commit()
        return None
