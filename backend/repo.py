from numu import bcrypt, db
from backend.models import User, Artist, Release, ArtistAka, UserRelease
from sqlalchemy.orm import joinedload


class Repo:
    def __init__(self, cache=None, autocommit=False):
        self._cache = cache
        self._autocommit = autocommit
        self._session = db.session
        self.did_commit = False

    def save(self, *argv):
        for obj in argv:
            db.session.add(obj)

        if self._autocommit:
            self.commit()

    def commit(self):
        self.did_commit = True
        db.session.commit()

    # -----------------------------------
    # Artist
    # -----------------------------------

    def get_artist_by_mbid(self, mbid):
        return Artist.query.filter_by(mbid=mbid).first()

    def get_artist_by_name(self, name):
        aka = ArtistAka.query.filter(ArtistAka.name.ilike(name)).first()
        if aka:
            artist = Artist.query.filter_by(mbid=aka.artist_mbid).first()
        else:
            artist = Artist.query.filter(Artist.name.ilike(name)).first()
        return artist


# --------------------------------------
# User
# --------------------------------------


def insert_user(email=None, icloud=None, password=None):
    hashed_password = None
    if password:
        hashed_password = bcrypt.generate_password_hash(password)

    new_user = User(password_hash=hashed_password, icloud=icloud, email=email)
    db.session.add(new_user)
    db.session.commit()

    return new_user


def get_user_by_email(email):
    users = User.query.filter_by(email=email)
    for user in users:
        return user
    return None


def get_user_by_icloud(icloud):
    users = User.query.filter_by(icloud=icloud)
    for user in users:
        return user
    return None


# --------------------------------------
# User Data
# --------------------------------------


def get_user_releases_unlistened(user_id):
    pass


# --------------------------------------
# Basic Fetch
# --------------------------------------


def get_numu_artist_by_mbid(mbid):
    return Artist.query.filter_by(mbid=mbid).first()


def get_numu_artist_by_name(name):
    aka = ArtistAka.query.filter(ArtistAka.name.ilike(name)).first()
    if aka:
        artist = Artist.query.filter_by(mbid=aka.artist_mbid).first()
    else:
        artist = Artist.query.filter(Artist.name.ilike(name)).first()
    return artist


def get_numu_release(release_mbid):
    return Release.query.filter_by(mbid=release_mbid).first()


def get_numu_artist_releases(artist_mbid):
    return (
        Artist.query.filter_by(mbid=artist_mbid)
        .options(joinedload("releases"))
        .first()
        .releases
    )

