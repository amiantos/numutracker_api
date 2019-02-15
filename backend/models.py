from sqlalchemy import (
    LargeBinary,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Index,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql.json import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, expression

from numu import db


class User(db.Model):
    id = Column(Integer, primary_key=True)
    email = Column(String(120), index=True, nullable=True, unique=True)
    icloud = Column(String(120), index=True, nullable=True, unique=True)
    password_hash = Column(LargeBinary(), nullable=True)
    date_joined = Column(DateTime(True), default=func.now())
    date_last_activity = Column(DateTime(True), default=func.now())
    date_v2_import = Column(DateTime(True), nullable=True)

    album = Column(Boolean(), default=True)
    single = Column(Boolean(), default=True)
    ep = Column(Boolean(), default=True)
    live = Column(Boolean(), default=False)
    soundtrack = Column(Boolean(), default=False)
    remix = Column(Boolean(), default=False)
    other = Column(Boolean(), default=False)

    artists = relationship("Artist", secondary="user_artist", lazy=True)
    releases = relationship("Release", secondary="user_release", lazy=True)

    @property
    def filters(self):
        filters = []
        if self.album:
            filters.append("Album")
        if self.single:
            filters.append("Single")
        if self.ep:
            filters.append("EP")
        if self.live:
            filters.append("Live")
        if self.soundtrack:
            filters.append("Soundtrack")
        if self.remix:
            filters.append("Remix")
        if self.other:
            filters.append("Other")
        return filters

    def __repr__(self):
        return "<User {}>".format(self.id)


class Artist(db.Model):
    __table_args__ = (
        Index("artist_name", "name"),
        Index("artist_sort_name", "sort_name"),
    )

    mbid = Column(String(36), primary_key=True)
    name = Column(String(512), nullable=False)
    sort_name = Column(String(512), nullable=False)
    disambiguation = Column(String(512), nullable=False)
    art = Column(
        Boolean(), nullable=False, default=False, server_default=expression.false()
    )

    date_added = Column(DateTime(True), nullable=False, default=func.now())
    date_art_check = Column(DateTime(True), nullable=True, default=None)
    date_checked = Column(DateTime(True), nullable=True, default=None)
    date_updated = Column(DateTime(True), nullable=False, default=func.now())

    links = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    users = relationship("User", secondary="user_artist", lazy=True)
    akas = relationship("ArtistAka", lazy=False)
    releases = relationship("Release", secondary="artist_release", lazy=True)

    def __repr__(self):
        return "<Artist {} - {}>".format(self.name, self.mbid)


class ArtistAka(db.Model):
    artist_mbid = Column(
        String(36),
        ForeignKey("artist.mbid", onupdate="CASCADE", ondelete="CASCADE"),
        index=True,
        primary_key=True,
    )
    name = Column(String(512), nullable=False, primary_key=True)

    def __repr__(self):
        return "<ArtistAka {} - {}>".format(self.artist_mbid, self.name)


class UserArtist(db.Model):
    uuid = Column(String(), unique=True, index=True, nullable=False)
    user_id = Column(
        Integer,
        ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    mbid = Column(
        String(36),
        ForeignKey(
            "artist.mbid",
            onupdate="CASCADE",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED",
        ),
        primary_key=True,
    )

    date_followed = Column(DateTime(True), nullable=False, default=func.now())
    follow_method = Column(String())
    following = Column(Boolean(), default=True, index=True)
    date_updated = Column(DateTime(True), nullable=False, default=func.now())

    user = relationship("User", lazy=True, uselist=False)
    artist = relationship("Artist", lazy=False)

    def __repr__(self):
        return "<UserArtist {} - {}>".format(self.user_id, self.mbid)


class ArtistRelease(db.Model):
    artist_mbid = Column(
        String(36),
        ForeignKey(
            "artist.mbid",
            onupdate="CASCADE",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED",
        ),
        primary_key=True,
        index=True,
    )
    release_mbid = Column(
        String(36),
        ForeignKey(
            "release.mbid",
            onupdate="CASCADE",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED",
        ),
        primary_key=True,
        index=True,
    )

    release = relationship("Release", lazy=False)


class Release(db.Model):
    mbid = Column(String(36), primary_key=True)
    title = Column(Text, nullable=False)
    artist_names = Column(Text, nullable=False)
    type = Column(String(36), index=True)
    art = Column(
        Boolean(), nullable=False, default=False, server_default=expression.false()
    )
    date_release = Column(Date(), nullable=False, index=True)
    links = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))

    date_added = Column(DateTime(True), nullable=False, default=func.now())
    date_art_check = Column(DateTime(True), nullable=True, default=None)
    date_checked = Column(DateTime(True), nullable=True, default=func.now())
    date_updated = Column(DateTime(True), nullable=False, default=func.now())

    artists = db.relationship("Artist", secondary="artist_release", lazy=False)

    def __repr__(self):
        return "<Release {} - {} - {}>".format(self.artist_names, self.title, self.mbid)


class UserRelease(db.Model):
    uuid = Column(String(), unique=True, index=True, nullable=False)
    user_id = Column(
        Integer,
        ForeignKey(
            "user.id",
            onupdate="CASCADE",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED",
        ),
        index=True,
        primary_key=True,
    )
    mbid = Column(
        String(36),
        ForeignKey(
            "release.mbid",
            onupdate="CASCADE",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED",
        ),
        primary_key=True,
    )

    listened = Column(Boolean(), default=False)
    date_listened = Column(DateTime(True), nullable=True, default=None)

    date_followed = Column(DateTime(True), nullable=False, default=func.now())
    follow_method = Column(String())
    following = Column(Boolean(), default=True, index=True)

    date_updated = Column(DateTime(True), nullable=False, default=func.now())

    release = relationship("Release", lazy=False)
    user = relationship("User", lazy=True, uselist=False)

    def __repr__(self):
        return "<UserRelease {}>".format(self.uuid)


class UserArtistImport(db.Model):
    user_id = Column(
        Integer,
        ForeignKey(
            "user.id",
            onupdate="CASCADE",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED",
        ),
        index=True,
        primary_key=True,
    )
    import_name = Column(Text, primary_key=True)
    import_mbid = Column(String(36), nullable=True)
    import_method = Column(String(36))
    found_mbid = Column(
        String(36),
        ForeignKey(
            "artist.mbid",
            onupdate="CASCADE",
            ondelete="SET NULL",
            deferrable=True,
            initially="DEFERRED",
        ),
        nullable=True,
    )

    date_added = Column(DateTime(True), nullable=False, default=func.now())
    date_checked = Column(DateTime(True), nullable=True, default=None)

    def __repr__(self):
        return "<UserArtistImport {} - {}>".format(self.user_id, self.import_name)


class UserNotification(db.Model):
    user_id = Column(
        Integer,
        ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    release_mbid = Column(
        String(36),
        ForeignKey(
            "release.mbid",
            onupdate="CASCADE",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED",
        ),
        primary_key=True,
    )
    type = Column(String(), index=True)
    date_created = Column(
        DateTime(True), index=True, nullable=False, default=func.now()
    )
    date_sent = Column(DateTime(True), nullable=True, default=None)

    release = relationship(Release, lazy=False, uselist=False)


class DeletedRelease(db.Model):
    mbid = Column(String(36), primary_key=True)
    date_deleted = Column(DateTime(True), nullable=False, default=func.now())
    meta = Column(String())


class DeletedArtist(db.Model):
    mbid = Column(String(36), primary_key=True)
    date_deleted = Column(DateTime(True), nullable=False, default=func.now())
    meta = Column(String())


class Lock(db.Model):
    process_name = Column(String(36), primary_key=True)
    lock_acquired = Column(Boolean())
    date_acquired = Column(DateTime(True))
