from sqlalchemy.sql import func

from backend.artists import ArtistProcessing
from backend import musicbrainz
from backend.models import Release, UserRelease
from backend.repo import Repo
from numu import app as numu_app
from backend import utils


class NotFoundError(Exception):
    pass


class ReleaseProcessing:
    def __init__(self, repo=None, mbz=None):
        self.repo = repo or Repo()
        self.mbz = mbz or musicbrainz
        self.logger = numu_app.logger
        self.artist_processor = ArtistProcessing(repo=self.repo, mbz=self.mbz)

    # ------------------------------------
    # Add
    # ------------------------------------

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
                # TODO: Might as well update the release here
                continue

            if release is None:
                self.logger.info("Release not found locally.")
                release = self._save_mb_release(mb_release)

            if release is not None:
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
            self.logger.info("Release does not qualify for inclusion")
            return None

        release = Release(
            mbid=mb_release.get("id"),
            title=mb_release.get("title"),
            type=utils.get_release_type(mb_release),
            date_release=date_release,
            artist_names=mb_release.get("artist-credit-phrase"),
            date_updated=func.now(),
        )

        self.repo.save(release)
        self.repo.commit()

        self.logger.info("New release saved: {}".format(release))

        for mb_artist in mb_release.get("artist-credit"):
            if type(mb_artist) == dict and mb_artist["artist"]:
                artist = self.artist_processor.add_artist(
                    mbid=mb_artist["artist"]["id"]
                )
                if artist and artist not in release.artists:
                    self.logger.info("Artist credit created for {}".format(artist))
                    release.artists.append(artist)

        self.repo.save(release)
        self.repo.commit()

        return release

    def add_user_release(self, user_artist, release):
        notify = False
        user_release = self.repo.get_user_release(user_artist.user_id, release.mbid)
        if user_release is None:
            user_release = UserRelease(
                uuid=utils.uuid(),
                user_artist_uuid=user_artist.uuid,
                user_id=user_artist.user_id,
                mbid=release.mbid,
            )
            notify = True
        user_release.title = release.title
        user_release.artist_names = release.artist_names
        user_release.type = release.type
        user_release.date_release = release.date_release
        user_release.art = release.art
        user_release.apple_music_link = release.apple_music_link
        user_release.spotify_link = release.spotify_link
        user_release.date_updated = release.date_updated

        self.repo.save(user_release)
        self.repo.commit()

        self.logger.info("New user release created {}".format(user_release))

        return user_release, notify

    def add_user_releases(self, user_artist, releases, notifications):
        for release in releases:
            user_release, notify = self.add_user_release(user_artist, release)
            if notifications and notify:
                # TODO: Create notification
                pass

    # ------------------------------------
    # Update
    # ------------------------------------

    def update_release(self, release):
        pass

    def update_user_release(self, release):
        pass

    def update_user_releases(self, artist, user_artist=None, notifications=True):
        releases = self.repo.get_releases_by_artist_mbid(artist.mbid)
        if user_artist:
            self.add_user_releases(user_artist, releases, notifications)
        else:
            user_artists = self.repo.get_user_artists_by_mbid(artist.mbid)
            for user_artist in user_artists:
                self.add_user_releases(user_artist, releases, notifications)
