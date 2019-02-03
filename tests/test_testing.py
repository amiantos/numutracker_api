from tests.model_factories import UserFactory
from backend.models import UserArtistImport
from backend.repo import Repo

from .test_api import BaseTestCase


class TestTesting(BaseTestCase):
    def setUp(self):
        self.repo = Repo(autocommit=True)
        self.user = UserFactory(email="info@numutracker.com")
        self.repo.save(self.user)

    def test_testing(self):
        imported = UserArtistImport(user_id=self.user.id, import_name="Nine Inch Nails")
        self.repo.save(imported)

        assert (
            UserArtistImport.query.filter_by(user_id=self.user.id).first().import_name
            == "Nine Inch Nails"
        )
