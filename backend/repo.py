from numu import bcrypt, db
from sqlalchemy import or_
from backend.models import (
    User,
    Artist,
    Release,
    ArtistAka,
    UserRelease,
    UserArtist,
    UserArtistImport,
    ArtistRelease,
    DeletedArtist,
)
from sqlalchemy.orm import joinedload
from sqlalchemy import and_


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

    def delete(self, *argv):
        for obj in argv:
            db.session.delete(obj)

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

    def get_user_artists_by_mbid(self, mbid, following=True):
        if following:
            return UserArtist.query.filter(
                UserArtist.mbid == mbid, UserArtist.following.is_(True)
            ).all()
        return UserArtist.query.filter_by(mbid=mbid).all()

    def get_user_artists_by_user_id(self, user_id):
        return UserArtist.query.filter_by(user_id=user_id).all()

    def get_user_artist(self, user_id, mbid):
        return UserArtist.query.filter_by(user_id=user_id, mbid=mbid).first()

    def delete_user_artists_by_mbid(self, mbid):
        return UserArtist.query.filter_by(mbid=mbid).delete()

    def update_user_artists(self, where, updates):
        """
        Update all user artists matching the where filter
        """
        UserArtist.query.filter_by(**where).update(updates)

    def get_deleted_artist(self, mbid):
        return DeletedArtist.query.filter_by(mbid=mbid).first()

    # -----------------------------------
    # Release
    # -----------------------------------

    def get_release_by_mbid(self, mbid):
        return Release.query.filter_by(mbid=mbid).first()

    def get_releases_by_artist_mbid(self, mbid):
        return (
            Artist.query.filter_by(mbid=mbid)
            .options(joinedload("releases"))
            .first()
            .releases
        )

    # -----------------------------------
    # Artist Release
    # -----------------------------------

    def get_artist_release(self, artist_mbid, release_mbid):
        return ArtistRelease.query.filter_by(
            artist_mbid=artist_mbid, release_mbid=release_mbid
        ).first()

    def get_artist_releases(self, mbid):
        return ArtistRelease.query.filter_by(artist_mbid=mbid).all()

    # -----------------------------------
    # User Release
    # -----------------------------------

    def get_user_release(self, user_id, mbid):
        return UserRelease.query.filter_by(user_id=user_id, mbid=mbid).first()

    def get_user_releases_for_artist(self, user, mbid):
        return (
            db.session.query(ArtistRelease, Release, UserRelease)
            .join(Release)
            .filter(ArtistRelease.artist_mbid == mbid, Release.type.in_(user.filters))
            .outerjoin(
                UserRelease,
                and_(UserRelease.mbid == Release.mbid, UserRelease.user_id == user.id),
            )
            .order_by(Release.date_release.desc())
            .all()
        ) or None

    def update_user_releases(self, where, updates):
        """
        Update all user releases matching the where filter
        """
        UserRelease.query.filter_by(**where).update(updates)

    # -----------------------------------
    # Artist Import
    # -----------------------------------

    def get_user_artist_imports(self, user_id):
        return UserArtistImport.query.filter(
            UserArtistImport.user_id == user_id,
            UserArtistImport.found_mbid.is_(None),
            UserArtistImport.date_checked.is_(None),
        ).all()

    def get_artist_import(self, user_id, name=None, mbid=None):
        if mbid and name:
            return UserArtistImport.query.filter(
                UserArtistImport.user_id == user_id,
                or_(
                    UserArtistImport.import_mbid == mbid,
                    UserArtistImport.import_name == name,
                ),
            ).first()
        if mbid:
            return UserArtistImport.query.filter_by(
                user_id=user_id, import_mbid=mbid
            ).first()
        return UserArtistImport.query.filter_by(
            user_id=user_id, import_name=name
        ).first()

    def get_artist_imports(self, date_filter, limit):
        return (
            UserArtistImport.query.filter(
                UserArtistImport.found_mbid.is_(None),
                or_(
                    UserArtistImport.date_checked < date_filter,
                    UserArtistImport.date_checked.is_(None),
                ),
            )
            .order_by(
                UserArtistImport.date_checked.asc().nullsfirst(),
                UserArtistImport.date_added.desc(),
            )
            .limit(limit)
            .all()
        )


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

