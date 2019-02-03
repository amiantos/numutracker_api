from uuid import uuid4

import backend.utils as utils
import factory
import factory.fuzzy
from backend.models import (
    Artist as ArtistModel,
    User as UserModel,
    UserArtist as UserArtistModel,
    UserArtistImport as ArtistImportModel,
)
from numu import db, bcrypt


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = UserModel
        sqlalchemy_session = db.session

    id = factory.Sequence(lambda n: n + 1)
    email = factory.fuzzy.FuzzyText(length=20, suffix="@example.com")
    icloud = None
    password_hash = b""
    date_joined = utils.now()
    date_last_activity = utils.now()

    album = True
    single = True
    ep = True
    live = False
    soundtrack = False
    remix = False
    other = False


class ArtistFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = ArtistModel
        sqlalchemy_session = db.session

    mbid = factory.fuzzy.FuzzyAttribute(lambda: utils.uuid())
    name = factory.Faker("name")
    sort_name = factory.SelfAttribute("name")
    disambiguation = factory.SelfAttribute("name")
    art = False
    date_added = utils.now()
    date_art_check = None
    date_checked = None
    date_updated = None
    apple_music_link = None
    spotify_link = None


class UserArtistFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = UserArtistModel
        sqlalchemy_session = db.session

    uuid = factory.fuzzy.FuzzyAttribute(lambda: utils.uuid())
    user_id = factory.SelfAttribute("user.id")
    mbid = factory.SelfAttribute("artist.mbid")
    name = factory.SelfAttribute("artist.name")
    sort_name = factory.SelfAttribute("artist.sort_name")
    date_updated = factory.SelfAttribute("artist.date_updated")

    date_followed = utils.now()
    follow_method = factory.fuzzy.FuzzyChoice(["V2", "apple", "spotify", "lastfm"])
    following = True

    user = factory.SubFactory(UserFactory)
    artist = factory.SubFactory(ArtistFactory)


class ArtistImportFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = ArtistImportModel
        sqlalchemy_session = db.session

    user_id = 0
    import_name = factory.Faker("name")
    import_mbid = factory.fuzzy.FuzzyAttribute(lambda: utils.uuid())
    import_method = "factory"
    found_mbid = None

    date_added = utils.now()
    date_checked = None
