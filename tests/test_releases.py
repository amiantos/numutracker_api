from tests.model_factories import (
    UserFactory,
    ArtistFactory,
    UserArtistFactory,
    ReleaseFactory,
    UserReleaseFactory,
)
from backend.releases import ReleaseProcessor
from backend.repo import Repo

from tests.test_api import BaseTestCase


class TestReleases(BaseTestCase):
    def setUp(self):
        self.repo = Repo(autocommit=True)
        self.release_processor = ReleaseProcessor(repo=self.repo)
        self.user = UserFactory(email="info@numutracker.com")
        self.artist = ArtistFactory(
            name="Tulsa", mbid="f123ef70-f563-43c2-b0e6-8f9afc0a38ad"
        )
        self.user_artist = UserArtistFactory(user=self.user, artist=self.artist)
        self.repo.save(self.user, self.artist)

    def test_add_release_from_mb(self):
        releases_added = self.release_processor.add_releases(self.artist)
        self.release_processor.update_user_releases(self.artist)

        user_releases = self.repo.get_user_releases_for_artist(
            self.user, self.artist.mbid
        )

        assert releases_added == 1
        assert len(user_releases) == 1

    def test_update_release_no_update(self):
        """When a release is updated with identical information, date_checked should update but not date_updated."""
        self.release_processor.add_release("dd5d8373-4ae3-3908-9235-c871e49ebd76")
        release = self.repo.get_release_by_mbid("dd5d8373-4ae3-3908-9235-c871e49ebd76")

        updated_release = self.release_processor.update_release(release)

        assert updated_release.date_updated != updated_release.date_checked

    def test_update_release_with_mock(self):
        release = ReleaseFactory(artist_names=self.artist.name)
        release.artists.append(self.artist)
        user_release = UserReleaseFactory(user=self.user, release=release)

        self.repo.save(user_release)

        mb_release = {
            "first-release-date": "2015-01-01",
            "title": "Random Title",
            "artist-credit-phrase": "Tulsa",
            "primary-type": "Album",
            "artist-credit": [{"artist": {}}],
        }

        self.release_processor._update_release(release, mb_release)

        release = self.repo.get_release_by_mbid(release.mbid)
        assert release.title == "Random Title"

        user_release = self.repo.get_user_release(self.user.id, release.mbid)
        assert user_release.release.title == "Random Title"

    def test_update_release_with_mock_delete(self):
        release = ReleaseFactory(artist_names=self.artist.name)
        release.artists.append(self.artist)
        self.repo.save(release)

        mb_release = {
            "first-release-date": "2015-01-01",
            "title": "Random Title",
            "artist-credit-phrase": "Tulsa",
            "primary-type": "Album",
        }

        self.release_processor._update_release(release, mb_release)

        release = self.repo.get_release_by_mbid(release.mbid)

        assert release is None

    def test_update_release_from_mb_with_followers_and_listeners(self):
        pass

    def test_delete_release_with_listeners(self):
        pass
