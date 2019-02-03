from backend.repo import Repo
from backend.artists import ArtistProcessing
from tests.model_factories import UserFactory, UserArtistFactory

from .test_api import BaseTestCase


class TestArtists(BaseTestCase):
    def setUp(self):
        self.repo = Repo(autocommit=True)
        self.artist_processing = ArtistProcessing(repo=self.repo)
        self.user = UserFactory(email="info@numutracker.com")
        self.repo.save(self.user)

    def test_add_artist_from_mb_by_name(self):
        artist = self.artist_processing.add_artist(name="Nine Inch Nails")
        assert artist.name == "Nine Inch Nails"

    def test_add_artist_from_mb_by_mbid(self):
        artist = self.artist_processing.add_artist(
            mbid="b7ffd2af-418f-4be2-bdd1-22f8b48613da"
        )
        assert artist.mbid == "b7ffd2af-418f-4be2-bdd1-22f8b48613da"

    def test_update_artist_from_mb_with_followers(self):
        user_artist = UserArtistFactory(user=self.user)
        self.repo.save(user_artist)
        artist = user_artist.artist

        new_data = {
            "name": "Foodly Boofer",
            "sort-name": "Boofer Foodly",
            "disambiguation": "Well known boofer of foodlies",
        }

        self.artist_processing._update_artist_data(artist, new_data)

        user_artists = self.repo.get_user_artists_by_user_id(self.user.id)
        artist = self.repo.get_artist_by_mbid(artist.mbid)

        assert user_artists[0].name == new_data["name"]
        assert artist.name == new_data["name"]
        assert artist.date_updated is not None

    def test_replace_artist_with_followers(self):
        pass

    def test_delete_artist_with_followers(self):
        user_artist = UserArtistFactory(user=self.user)
        self.repo.save(user_artist)
        artist_mbid = user_artist.artist.mbid

        self.artist_processing.delete_artist(user_artist.artist)
        user_artists = self.repo.get_user_artists_by_user_id(self.user.id)
        artist = self.repo.get_artist_by_mbid(artist_mbid)

        assert len(user_artists) == 0
        assert artist is None
