from .test_api import BaseTestCase

from backend import musicbrainz as mbz


class TestMusicbrainz(BaseTestCase):
    def setUp(self):
        pass

    def test_search_artist_by_name(self):
        result = mbz.search_artist_by_name("Nine Inch Nails")
        assert result.get("status") == 200
        assert result.get("artist").get("id") == "b7ffd2af-418f-4be2-bdd1-22f8b48613da"

    def test_get_artist(self):
        result = mbz.get_artist("b7ffd2af-418f-4be2-bdd1-22f8b48613da")
        assert result.get("status") == 200
        assert result.get("artist").get("id") == "b7ffd2af-418f-4be2-bdd1-22f8b48613da"

    def test_get_release(self):
        result = mbz.get_release("fcb872a2-7ef9-3ed0-bd4a-7c55c78179b6")
        assert result.get("status") == 200
        assert result.get("release").get("id") == "fcb872a2-7ef9-3ed0-bd4a-7c55c78179b6"

    def test_get_artist_releases(self):
        # Uses the artist Tulsa, defunct band should only have 1 release.
        # https://musicbrainz.org/artist/f123ef70-f563-43c2-b0e6-8f9afc0a38ad
        result = mbz.get_artist_releases("f123ef70-f563-43c2-b0e6-8f9afc0a38ad")
        assert len(result.get("releases")) == 1
