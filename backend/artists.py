from sqlalchemy.sql import func

from backend import musicbrainz as mbz
from backend.models import Artist
from backend.repo import Repo


class ArtistProcessing:
    def __init__(self, repo=None):
        self.repo = repo or Repo()

    def add_artist(self, name=None, mbid=None):
        artist = None

        if mbid:
            artist = self._add_artist_by_mbid(mbid)

        if name and artist is None:
            artist = self._add_artist_by_name(name)

        return artist

    def _add_artist_by_mbid(self, mbid):
        mb_result = mbz.get_artist(mbid)

        return self._process_mb_result(mb_result)

    def _add_artist_by_name(self, name):
        mb_result = mbz.search_artist_by_name(name)

        return self._process_mb_result(mb_result)

    def _process_mb_result(self, mb_result):
        if mb_result.get("status", 0) != 200:
            return None

        mb_artist = mb_result.get("artist")
        artist = self.repo.get_artist_by_mbid(mb_artist.get("id"))
        if artist is not None:
            return artist

        return self._save_artist_from_mb(mb_artist)

    def _save_artist_from_mb(self, mb_artist):
        artist = Artist(
            mbid=mb_artist.get("id"),
            name=mb_artist.get("name"),
            sort_name=mb_artist.get("sort-name"),
            disambiguation=mb_artist.get("disambiguation", ""),
            date_updated=func.now(),
        )
        self.repo.save(artist)
        self.repo.commit()

        return artist
