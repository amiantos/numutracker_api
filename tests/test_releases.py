from tests.model_factories import UserFactory, ArtistFactory, UserArtistFactory
from backend.releases import ReleaseProcessing
from backend.repo import Repo

from .test_api import BaseTestCase


class TestReleases(BaseTestCase):
    def setUp(self):
        self.repo = Repo(autocommit=True)
        self.release_processing = ReleaseProcessing(repo=self.repo)
        self.user = UserFactory(email="info@numutracker.com")
        self.artist = ArtistFactory(
            name="Tulsa", mbid="f123ef70-f563-43c2-b0e6-8f9afc0a38ad"
        )
        self.user_artist = UserArtistFactory(user=self.user, artist=self.artist)
        self.repo.save(self.user, self.artist)

    def test_add_release_from_mb(self):
        releases_added = self.release_processing.add_releases(self.artist)
        self.release_processing.update_user_releases(self.artist)

        user_releases = self.repo.get_user_releases_for_artist(
            self.user.id, self.artist.mbid
        )

        assert releases_added == 1
        assert len(user_releases) == 1

    def test_add_release_from_mb_with_followers(self):
        pass

    def test_update_release_from_mb_with_followers_and_listeners(self):
        pass

    def test_delete_release_with_listeners(self):
        pass
