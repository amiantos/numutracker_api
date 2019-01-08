from .test_api import BaseTestCase

from numu import db

from backend.models import User, ArtistImport


class TestTesting(BaseTestCase):
    def setUp(self):
        self.user = User(email="brad@root.com")
        db.session.add(self.user)
        db.session.commit()

    def test_testing(self):
        imported = ArtistImport(user_id=self.user.id, import_name="Nine Inch Nails")
        db.session.add(imported)
        db.session.commit()

        assert ArtistImport.query.filter_by(user_id=self.user.id).first().import_name == "Nine Inch Nails"