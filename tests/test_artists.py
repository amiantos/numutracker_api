from backend.repo import Repo
from backend.artists import ArtistProcessor
from tests.model_factories import (
    ArtistFactory,
    UserFactory,
    UserArtistFactory,
    ReleaseFactory,
    UserReleaseFactory,
)
from backend import utils

from tests.test_api import BaseTestCase


class TestArtists(BaseTestCase):
    def setUp(self):
        self.repo = Repo(autocommit=True)
        self.artist_processor = ArtistProcessor(repo=self.repo)
        self.user = UserFactory(email="info@numutracker.com")
        self.repo.save(self.user)

    def test_add_artist_from_mb_by_name(self):
        artist = self.artist_processor.add_artist(name="Nine Inch Nails")
        assert artist.name == "Nine Inch Nails"

    def test_add_artist_from_mb_by_mbid(self):
        artist = self.artist_processor.add_artist(
            mbid="b7ffd2af-418f-4be2-bdd1-22f8b48613da"
        )
        assert artist.mbid == "b7ffd2af-418f-4be2-bdd1-22f8b48613da"

    def test_update_artist_data_with_followers(self):
        user_artist = UserArtistFactory(user=self.user)
        self.repo.save(user_artist)
        artist = user_artist.artist

        new_data = {
            "name": "Foodly Boofer",
            "sort-name": "Boofer Foodly",
            "disambiguation": "Well known boofer of foodlies",
        }

        self.artist_processor._update_artist_data(artist, new_data)

        artist = self.repo.get_artist_by_mbid(artist.mbid)

        assert artist.name == new_data["name"]
        assert artist.date_updated is not None

    def test_update_artist_from_mb_mocked(self):
        user_artist = UserArtistFactory(user=self.user)
        self.repo.save(user_artist)
        artist = user_artist.artist
        original_name = artist.name

        mb_result_mock = {
            "status": 200,
            "artist": {
                "id": artist.mbid,
                "name": "Brad Root",
                "sort-name": "Root Brad",
                "disambiguation": "Cool guy from Los Angeles",
            },
        }

        updated_artist = self.artist_processor._update_artist(artist, mb_result_mock)
        assert updated_artist.name == "Brad Root"

        artist = self.repo.get_artist_by_name(original_name)
        assert artist is None

        user_artists = self.repo.get_user_artists_by_user_id(self.user.id)
        assert len(user_artists) == 1

    def test_update_artist_from_mb_mocked_new_mbid(self):
        user_artist = UserArtistFactory(user=self.user)
        self.repo.save(user_artist)
        artist = user_artist.artist
        new_mbid = utils.uuid()

        mb_result_mock = {
            "status": 200,
            "artist": {
                "id": new_mbid,
                "name": artist.name,
                "sort-name": artist.sort_name,
                "disambiguation": artist.disambiguation,
            },
        }

        updated_artist = self.artist_processor._update_artist(artist, mb_result_mock)
        assert updated_artist.name == artist.name
        assert updated_artist.mbid == new_mbid

        user_artists = self.repo.get_user_artists_by_user_id(self.user.id)
        assert len(user_artists) == 1
        assert user_artists[0].mbid == new_mbid

    def test_update_artist_from_mb_mocked_removed(self):
        user_artist = UserArtistFactory(user=self.user)
        self.repo.save(user_artist)

        mb_result_mock = {"status": 404}

        updated_artist = self.artist_processor._update_artist(
            user_artist.artist, mb_result_mock
        )
        assert updated_artist is None

        user_artists = self.repo.get_user_artists_by_user_id(self.user.id)
        assert len(user_artists) == 0

    def test_replace_artist_with_followers(self):
        user_artist = UserArtistFactory(user=self.user)
        self.repo.save(user_artist)

        new_artist = ArtistFactory()

        self.artist_processor.replace_artist(user_artist.artist, new_artist)

        user_artists = self.repo.get_user_artists_by_user_id(self.user.id)
        assert len(user_artists) == 1
        assert user_artists[0].mbid == new_artist.mbid

    def test_replace_artist_with_followers_and_listeners(self):
        user_artist = UserArtistFactory(user=self.user)
        artist = user_artist.artist
        release = ReleaseFactory(artist_names=artist.name, artists=[artist])
        user_release = UserReleaseFactory(release=release, user=self.user)
        new_artist = ArtistFactory(name=artist.name)
        self.repo.save(user_release, new_artist)

        user_releases = self.repo.get_user_releases_for_artist(self.user, artist.mbid)
        assert len(user_releases) == 1

        user_artist = self.repo.get_user_artist(self.user.id, artist.mbid)
        assert user_artist.artist.name == artist.name

        self.artist_processor.replace_artist(artist, new_artist)

        user_releases = self.repo.get_user_releases_for_artist(
            self.user, new_artist.mbid
        )
        assert len(user_releases) == 1

        user_artist = self.repo.get_user_artist(self.user.id, new_artist.mbid)
        assert user_artist.artist.name == artist.name

        user_artists = self.repo.get_user_artists_by_user_id(self.user.id)
        assert len(user_artists) == 1

    def test_replace_artist_with_followers_and_listeners_already_exists(self):
        user_artist = UserArtistFactory(user=self.user)
        artist = user_artist.artist
        release = ReleaseFactory(artist_names=artist.name, artists=[artist])
        user_release = UserReleaseFactory(release=release, user=self.user)
        new_artist = ArtistFactory(name=artist.name)
        new_user_artist = UserArtistFactory(user=self.user, artist=new_artist)
        self.repo.save(user_release, new_user_artist)

        self.artist_processor.replace_artist(artist, new_artist)

        user_artist = self.repo.get_user_artist(self.user.id, new_artist.mbid)
        assert user_artist.artist.name == artist.name

    def test_delete_artist_with_followers(self):
        user_artist = UserArtistFactory(user=self.user)
        artist = user_artist.artist
        release = ReleaseFactory(artist_names=artist.name, artists=[artist])
        user_release = UserReleaseFactory(release=release, user=self.user)
        new_artist = ArtistFactory(name=artist.name)
        self.repo.save(user_release, new_artist)

        artist_mbid = user_artist.artist.mbid

        self.artist_processor.delete_artist(user_artist.artist, "test deletion")

        artist_releases = self.repo.get_artist_releases(artist_mbid)
        assert len(artist_releases) == 0

        user_artists = self.repo.get_user_artists_by_user_id(self.user.id)
        assert len(user_artists) == 0

        artist = self.repo.get_artist_by_mbid(artist_mbid)
        assert artist is None

        user_artist_releases = self.repo.get_user_releases_for_artist(
            self.user, artist_mbid
        )
        assert user_artist_releases is None

        raise Exception
