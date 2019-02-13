from datetime import datetime, timedelta

from sqlalchemy.sql import func

from backend import musicbrainz
from backend.models import UserArtistImport
from backend.artists import ArtistProcessor
from backend.releases import ReleaseProcessor
from backend.repo import Repo
from backend import utils
from numu import app as numu_app


class ImportProcessor:
    def __init__(self, repo=None, mbz=None):
        self.repo = repo or Repo()
        self.mbz = mbz or musicbrainz
        self.logger = numu_app.logger
        self.artist_processor = ArtistProcessor(repo=repo, mbz=self.mbz)
        self.release_processor = ReleaseProcessor(repo=repo, mbz=self.mbz)

    def import_from_lastfm(
        self, user_id, lastfm_username, limit=500, period="overall", page=1
    ):
        """Download artists from a LastFM account into the user's library.

        Period options: overall | 7day | 1month | 3month | 6month | 12month"""

        data = utils.grab_json(
            "http://ws.audioscrobbler.com/2.0/?method=user.gettopartists"
            + "&user={}&limit={}&api_key={}&period={}&page={}&format=json".format(
                lastfm_username,
                limit,
                numu_app.config.get("LAST_FM_API_KEY"),
                period,
                page,
            )
        )
        artists_list = []
        for artist in data.get("topartists", {}).get("artist"):
            artists_list.append({"name": artist["name"], "mbid": artist["mbid"]})

        return self.save_imports(user_id, artists_list, import_method="lastfm")

    def save_imports(self, user_id, artists_list, import_method):
        validated_artists = []
        for artist in artists_list:
            try:
                artist_name = str(artist["name"]) if artist.get("name") else None
                artist_mbid = str(artist["mbid"]) if artist.get("mbid") else None
                if artist_name or artist_mbid:
                    validated_artists.append({"name": artist_name, "mbid": artist_mbid})
            except ValueError:
                pass

        if len(validated_artists) == 0:
            return 0

        artists_added = 0

        for artist in validated_artists:
            found_import = self.repo.get_artist_import(
                user_id, name=artist["name"], mbid=artist["mbid"]
            )
            if found_import is None:
                new_import = UserArtistImport(
                    user_id=user_id,
                    import_name=artist["name"],
                    import_mbid=artist["mbid"],
                    import_method=import_method,
                )
                self.repo.save(new_import)
                artists_added += 1

        if artists_added > 0:
            self.repo.commit()

        return artists_added

    def import_user_artists(self, check_musicbrainz=True, user_id=None):
        date_filter = datetime.now() - timedelta(days=14)
        limit = 5000
        if check_musicbrainz:
            limit = 100

        if user_id:
            artist_imports = self.repo.get_user_artist_imports(user_id)
        else:
            artist_imports = self.repo.get_artist_imports(date_filter, limit)

        for artist_import in artist_imports:
            found_artist = self._find_artist(artist_import, check_musicbrainz)

            if found_artist is not None:
                self.logger.info("Found artist {}".format(found_artist))
                artist_import.found_mbid = found_artist.mbid
                self._create_user_artist(
                    artist_import.user_id, artist_import.import_method, found_artist
                )
            else:
                self.logger.info("Did not find artist")
                if check_musicbrainz:
                    artist_import.date_checked = func.now()

            self.repo.save(artist_import)
            self.repo.commit()

    def _find_artist(self, artist_import, check_musicbrainz):
        found_artist = None
        self.logger.info(
            "Checking artist import {} - {}".format(
                artist_import.user_id, artist_import.import_name
            )
        )

        self.logger.info("Searching by MBID")
        found_artist = self.repo.get_artist_by_mbid(artist_import.import_mbid)

        if found_artist is None:
            self.logger.info("Searching by name")
            found_artist = self.repo.get_artist_by_name(artist_import.import_name)

        if found_artist is None and check_musicbrainz:
            self.logger.info("Searching MusicBrainz")
            found_artist = self.artist_processor.add_artist(
                name=artist_import.import_name, mbid=artist_import.import_mbid
            )
            if found_artist:
                self.release_processor.add_releases(found_artist)

        return found_artist

    def _create_user_artist(self, user_id, import_method, artist):
        user_artist = self.artist_processor.add_or_update_user_artist(
            user_id, artist, import_method
        )
        self.release_processor.update_user_releases(artist, user_artist, False)
