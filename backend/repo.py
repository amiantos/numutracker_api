from numu import bcrypt, db
from backend.models import User, Artist, Release, ArtistAka
from sqlalchemy.orm import joinedload


# --------------------------------------
# User
# --------------------------------------

def insert_user(email=None, icloud=None, password=None):
    hashed_password = None
    if password:
        hashed_password = bcrypt.generate_password_hash(password)

    new_user = User(
        password_hash=hashed_password,
        icloud=icloud,
        email=email)
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
# Basic Fetch
# --------------------------------------


def get_numu_artist_by_mbid(mbid):
    return Artist.query.filter_by(mbid=mbid).first()


def get_numu_artist_by_name(name):
    aka = ArtistAka.query.filter(
        ArtistAka.name.ilike("{}".format(name))).first()
    if aka:
        artist = Artist.query.filter_by(mbid=aka.artist_mbid).first()
    else:
        artist = Artist.query.filter(
            Artist.name.ilike("{}".format(name))).first()
    return artist


def get_numu_release(release_mbid):
    return Release.query.filter_by(mbid=release_mbid).first()


def get_numu_artist_releases(artist_mbid):
    return Artist.query.filter_by(mbid=artist_mbid).options(joinedload('releases')).first().releases