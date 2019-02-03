from backend.repo import Repo
from backend.artists import ArtistProcessor
from backend.user_artists import ImportProcessor
from tests.model_factories import (
    ArtistFactory,
    UserFactory,
    UserArtistFactory,
    ArtistImportFactory,
)

from tests.test_api import BaseTestCase


class TestUserArtists(BaseTestCase):
    def setUp(self):
        self.repo = Repo(autocommit=True)
        self.artist_processor = ArtistProcessor(repo=self.repo)
        self.import_processor = ImportProcessor(repo=self.repo)
        self.user = UserFactory(email="info@numutracker.com")
        self.repo.save(self.user)

    # ------------------------------------
    # Saving Imports
    # ------------------------------------

    def test_save_imports(self):
        artists = ["Eels", "Nine Inch Nails", "Spoon"]
        artists_added = self.import_processor.save_imports(
            self.user.id, artists, "test"
        )
        artist_import = self.repo.get_artist_import(self.user.id, "Nine Inch Nails")
        assert artists_added == 3
        assert artist_import.import_name == "Nine Inch Nails"

    def test_save_imports_empty(self):
        artists = []
        artists_added = self.import_processor.save_imports(
            self.user.id, artists, "test"
        )
        assert artists_added == 0

    def test_save_imports_existing(self):
        artist_import = ArtistImportFactory(
            user_id=self.user.id,
            import_name="Nine Inch Nails",
            import_mbid="b7ffd2af-418f-4be2-bdd1-22f8b48613da",
        )
        self.repo.save(artist_import)
        artists = ["Nine Inch Nails"]
        artists_added = self.import_processor.save_imports(
            self.user.id, artists, "test"
        )
        assert artists_added == 0

    # ------------------------------------
    # Processing Imports
    # ------------------------------------

    def test_import_user_artists_no_mb(self):
        artist = ArtistFactory(
            mbid="b7ffd2af-418f-4be2-bdd1-22f8b48613da", name="Nine Inch Nails"
        )
        artist_import = ArtistImportFactory(
            user_id=self.user.id,
            import_name="Nine Inch Nails",
            import_mbid="b7ffd2af-418f-4be2-bdd1-22f8b48613da",
        )
        self.repo.save(artist, artist_import)
        self.import_processor.import_user_artists(
            check_musicbrainz=False, user_id=self.user.id
        )
        user_artist = self.repo.get_user_artist(
            user_id=self.user.id, mbid="b7ffd2af-418f-4be2-bdd1-22f8b48613da"
        )
        assert user_artist.name == "Nine Inch Nails"

    def test_import_user_artists_all_no_mb(self):
        artist = ArtistFactory(
            mbid="b7ffd2af-418f-4be2-bdd1-22f8b48613da", name="Nine Inch Nails"
        )
        artist_import = ArtistImportFactory(
            user_id=self.user.id,
            import_name="Nine Inch Nails",
            import_mbid="b7ffd2af-418f-4be2-bdd1-22f8b48613da",
        )
        self.repo.save(artist, artist_import)
        self.import_processor.import_user_artists(check_musicbrainz=False)
        user_artist = self.repo.get_user_artist(
            user_id=self.user.id, mbid="b7ffd2af-418f-4be2-bdd1-22f8b48613da"
        )
        assert user_artist.name == "Nine Inch Nails"

    def test_import_user_artists_all_no_mb_not_found(self):
        artist_import = ArtistImportFactory(
            user_id=self.user.id,
            import_name="Nine Inch Nails",
            import_mbid="b7ffd2af-418f-4be2-bdd1-22f8b48613da",
        )
        self.repo.save(artist_import)
        self.import_processor.import_user_artists(check_musicbrainz=False)
        user_artist = self.repo.get_user_artist(
            user_id=self.user.id, mbid="b7ffd2af-418f-4be2-bdd1-22f8b48613da"
        )
        assert user_artist is None

    def test_import_user_artists_with_mb(self):
        artist_import = ArtistImportFactory(
            user_id=self.user.id,
            import_name="Tulsa",
            import_mbid="f123ef70-f563-43c2-b0e6-8f9afc0a38ad",
        )
        self.repo.save(artist_import)
        self.import_processor.import_user_artists(
            check_musicbrainz=True, user_id=self.user.id
        )
        user_artist = self.repo.get_user_artist(
            user_id=self.user.id, mbid="f123ef70-f563-43c2-b0e6-8f9afc0a38ad"
        )
        user_releases = self.repo.get_user_releases_for_artist(
            user_id=self.user.id, mbid="f123ef70-f563-43c2-b0e6-8f9afc0a38ad"
        )
        assert user_artist.name == "Tulsa"
        assert len(user_releases) > 0
