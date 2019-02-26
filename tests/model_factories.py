import backend.utils as utils
import factory
import factory.fuzzy
from backend.models import (
    Artist as ArtistModel,
    Release as ReleaseModel,
    User as UserModel,
    UserArtist as UserArtistModel,
    UserArtistImport as UserArtistImportModel,
    UserRelease as UserReleaseModel,
)
from numu import db


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
    disambiguation = factory.fuzzy.FuzzyText(length=12)
    art = False
    date_added = utils.now()
    date_art_check = None
    date_checked = None
    date_updated = None
    links = {}


class ReleaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = ReleaseModel
        sqlalchemy_session = db.session

    mbid = factory.fuzzy.FuzzyAttribute(lambda: utils.uuid())
    title = factory.fuzzy.FuzzyText(length=12)
    artist_names = factory.Faker("name")
    type = "Album"
    art = False
    date_release = "2019-02-03"


class UserReleaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = UserReleaseModel
        sqlalchemy_session = db.session

    user_id = factory.SelfAttribute("user.id")
    mbid = factory.SelfAttribute("release.mbid")

    user = factory.SubFactory(UserFactory)
    release = factory.SubFactory(ReleaseFactory)


class UserArtistFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = UserArtistModel
        sqlalchemy_session = db.session

    user_id = factory.SelfAttribute("user.id")
    mbid = factory.SelfAttribute("artist.mbid")

    date_followed = utils.now()
    follow_method = factory.fuzzy.FuzzyChoice(["V2", "apple", "spotify", "lastfm"])
    following = True

    user = factory.SubFactory(UserFactory)
    artist = factory.SubFactory(ArtistFactory)


class ArtistImportFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = UserArtistImportModel
        sqlalchemy_session = db.session

    user_id = 0
    import_name = factory.Faker("name")
    import_mbid = factory.fuzzy.FuzzyAttribute(lambda: utils.uuid())
    import_method = "factory"
    found_mbid = None

    date_added = utils.now()
    date_checked = None
