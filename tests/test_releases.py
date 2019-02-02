from backend.models import ArtistImport, User
from backend.repo import Repo

from .test_api import BaseTestCase


class TestReleases(BaseTestCase):
    def setUp(self):
        self.repo = Repo(autocommit=True)
        self.user = User(email="info@numutracker.com")
        self.repo.save(self.user)
    
    def test_add_release_from_mb(self):
        pass
    
    def test_add_release_from_mb_with_followers(self):
        pass
    
    def test_update_release_from_mb_with_followers_and_listeners(self):
        pass
    
    def test_delete_release_with_listeners(self):
        pass

    def test_testing(self):
        imported = ArtistImport(user_id=self.user.id, import_name="Nine Inch Nails")
        self.repo.save(imported)
        assert ArtistImport.query.filter_by(user_id=self.user.id).first().import_name == "Nine Inch Nails"
