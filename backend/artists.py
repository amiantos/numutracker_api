from sqlalchemy.sql import func

from backend import musicbrainz
from backend.models import Artist, UserArtist
from backend.repo import Repo
from backend import utils
from numu import app as numu_app


class NotFoundError(Exception):
    pass


class ArtistProcessor:
    def __init__(self, repo=None, mbz=None):
        self.repo = repo or Repo()
        self.mbz = mbz or musicbrainz
        self.logger = numu_app.logger

    def _extract_artist_from_mb_result(self, mb_result):
        result_status = mb_result.get("status")
        if result_status == 404:
            raise NotFoundError

        if result_status == 200:
            return mb_result.get("artist")

        raise Exception

    # ------------------------------------
    # Artist: Add
    # ------------------------------------

    def add_artist(self, name=None, mbid=None):
        artist = None

        if mbid:
            artist = self.repo.get_artist_by_mbid(mbid)
            if artist is not None:
                self.logger.info("Artist {} found locally.".format(artist.name))
                return artist
            artist = self._add_artist_by_mbid(mbid)

        if name and artist is None:
            artist = self._add_artist_by_name(name)

        return artist

    def _add_artist_by_mbid(self, mbid):
        mb_result = self.mbz.get_artist(mbid)

        return self._process_mb_result(mb_result)

    def _add_artist_by_name(self, name):
        mb_result = self.mbz.search_artist_by_name(name)

        return self._process_mb_result(mb_result)

    def _process_mb_result(self, mb_result):
        try:
            mb_artist = self._extract_artist_from_mb_result(mb_result)
        except NotFoundError as e:
            self.logger.error("Artist not found in MusicBrainz")
            return None
        except Exception as e:
            self.logger.error("Unknown Musicbrainz Error Occurred")
            raise e

        return self._save_mb_artist(mb_artist)

    def _save_mb_artist(self, mb_artist):
        artist = self.repo.get_artist_by_mbid(mb_artist.get("id"))
        if artist is not None:
            self.logger.info("Artist {} found locally.".format(artist.name))
            return artist

        artist = Artist(
            mbid=mb_artist.get("id"),
            name=mb_artist.get("name"),
            sort_name=mb_artist.get("sort-name"),
            disambiguation=mb_artist.get("disambiguation", ""),
            date_updated=func.now(),
        )
        self.repo.save(artist)
        self.repo.commit()

        self.logger.info("New artist added: {}".format(artist))

        return artist

    # ------------------------------------
    # Artist: Update
    # ------------------------------------

    def update_artist(self, artist):
        mb_result = self.mbz.get_artist(artist.mbid)
        return self._update_artist(artist, mb_result)

    def _update_artist(self, artist, mb_result):
        try:
            mb_artist = self._extract_artist_from_mb_result(mb_result)
        except NotFoundError as e:
            self.logger.error(
                "Artist {} has been removed from Musicbrainz".format(artist)
            )
            self.delete_artist(artist)
            return None
        except Exception as e:
            self.logger.error("Unknown Musicbrainz Error Occurred")
            raise e

        if mb_artist["id"] != artist.mbid:
            new_artist = self._save_mb_artist(mb_artist)
            self.replace_artist(artist, new_artist)
            artist = new_artist

        if mb_artist:
            artist = self._update_artist_data(artist, mb_artist)

        return artist

    def _update_artist_data(self, artist, mb_artist):
        has_artist_changed = (
            artist.name != mb_artist["name"]
            or artist.sort_name != mb_artist["sort-name"]
            or artist.disambiguation != mb_artist.get("disambiguation", "")
            or artist.date_updated is None
        )

        if has_artist_changed:
            artist.name = mb_artist["name"]
            artist.sort_name = mb_artist["sort-name"]
            artist.disambiguation = mb_artist.get("disambiguation", "")
            artist.date_updated = func.now()
            self.repo.save(artist)
            self.repo.commit()

            self.update_user_artists(artist)

        return artist

    def update_user_artists(self, artist):
        self.repo.update_user_artists(
            {"mbid": artist.mbid},
            {
                "name": artist.name,
                "sort_name": artist.sort_name,
                "date_updated": artist.date_updated,
            },
        )
        self.repo.commit()

    # ------------------------------------
    # Artist: Replace
    # ------------------------------------

    def replace_artist(self, artist, new_artist):
        self.logger.error(
            "Replacing Artist: {} is being replaced by {}".format(artist, new_artist)
        )
        # Update all artist_releases
        artist_releases = self.repo.get_artist_releases(artist.mbid)
        for artist_release in artist_releases:
            artist_release.artist_mbid = new_artist.mbid
            self.repo.save(artist_release)
        self.repo.commit()

        # Update all user_artists
        user_artists = self.repo.get_user_artists_by_mbid(artist.mbid)
        for user_artist in user_artists:
            new_user_artist = self.repo.get_user_artist(
                user_artist.user_id, new_artist.mbid
            )
            if new_user_artist:
                continue

            user_artist.mbid = new_artist.mbid
            user_artist.name = new_artist.name
            user_artist.sort_name = new_artist.sort_name
            self.repo.save(user_artist)
        self.repo.commit()

        self.delete_artist(artist)

    # ------------------------------------
    # Artist: Delete
    # ------------------------------------

    def delete_artist(self, artist):
        self.repo.delete_user_artists_by_mbid(artist.mbid)
        self.repo.delete(artist)
        self.repo.commit()

    # ------------------------------------
    # User Artist
    # ------------------------------------

    def add_or_update_user_artist(self, user_id, artist, import_method):
        user_artist = self.repo.get_user_artist(user_id, artist.mbid)
        if user_artist is None:
            user_artist = UserArtist(
                uuid=utils.uuid(),
                user_id=user_id,
                mbid=artist.mbid,
                follow_method=import_method,
                date_followed=func.now(),
                following=True,
            )
        user_artist.name = artist.name
        user_artist.sort_name = artist.sort_name
        user_artist.date_updated = func.now()

        self.repo.save(user_artist)
        self.repo.commit()

        return user_artist
