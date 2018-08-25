import enum

from itsdangerous import BadSignature, SignatureExpired
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from passlib.apps import custom_app_context as pwd_context
from sqlalchemy import (Boolean, Column, DateTime, Enum, ForeignKey, Integer,
                        Numeric, String, JSON)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import expression, func

from main import app, db


class ReleaseType(enum.Enum):
    ALBUM = 'Album'
    AUDIOBOOK = 'Audiobook'
    BROADCAST = 'Broadcast'
    COMPILATION = 'Compilation'
    DEMO = 'Demo'
    DJ_MIX = 'DJ-mix'
    EP = 'EP'
    INTERVIEW = 'Interview'
    LIVE = 'Live'
    MIX_TAPE = 'Mix-tape'
    OTHER = 'Other'
    REMIX = 'Remix'
    SINGLE = 'Single'
    SOUNDTRACK = 'Soundtrack'
    SPOKENWORD = 'Spokenword'
    UNKNOWN = 'Unknown'


class AddMethod(enum.Enum):
    AUTOMATIC = 'Automatic'
    MANUAL = 'Manual'
    LISTENED = 'Listened'


class ImportMethod(enum.Enum):
    APPLE = "Apple Music"
    SPOTIFY = "Spotify"
    LASTFM = "Last.FM"


class NotificationType(enum.Enum):
    PAST = "Past Release"
    UPCOMING = "Upcoming Release"
    RECENT = "Recent Release"
    RELEASED = "New Release"


class ActivityTypes(enum.Enum):
    LISTENED = "Listened to Release"
    UNLISTENED = "Removed Listen Status"
    FOLLOW_ARTIST = "Followed Artist"
    FOLLOW_RELEASE = "Followed Release"
    UNFOLLOW_ARTIST = "Unfollowed Artist"
    UNFOLLOW_RELEASE = "Unfollowed Release"
    APPLE_IMPORT = "Imported from Apple Music"
    SPOTIFY_IMPORT = "Imported from Spotify"
    LASTFM_IMPORT = "Imported from Last.FM"
    COMMENT_ARTIST = "Commented on Artist"
    COMMENT_RELEASE = "Commented on Release"
    RATED_RELEASE = "Rated a Release"


class User(db.Model):
    id = Column(Integer, primary_key=True)
    email = Column(String(120), index=True, unique=True)
    password_hash = Column(String(128))
    username = Column(String(12), nullable=True, unique=True)
    date_joined = Column(DateTime(True), server_default=func.now(),
                         default=func.now())
    album = Column(Boolean(), server_default=expression.true(), default=True)
    single = Column(Boolean(), server_default=expression.true(), default=True)
    ep = Column(Boolean(), server_default=expression.true(), default=True)
    live = Column(Boolean(), server_default=expression.false(), default=False)
    soundtrack = Column(Boolean(), server_default=expression.false(),
                        default=False)
    remix = Column(Boolean(), server_default=expression.false(), default=False)
    other = Column(Boolean(), server_default=expression.false(), default=False)

    artists = relationship("Artist", secondary="user_artist", lazy=True)
    releases = relationship("Release", secondary="user_release", lazy=True)

    def __repr__(self):
        return '<User {}>'.format(self.id)

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None    # valid token, but expired
        except BadSignature:
            return None    # invalid token
        user = User.query.get(data['id'])
        return user


class UserActivity(db.Model):
    id = Column(
        Integer,
        primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey(
            'user.id',
            onupdate="CASCADE",
            ondelete="CASCADE"))
    date = Column(
        DateTime(True),
        server_default=func.now(),
        default=func.now())
    release_mbid = Column(
        String(36),
        ForeignKey(
            'release.mbid',
            onupdate="CASCADE",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED"),
        nullable=True)
    artist_mbid = Column(
        String(36),
        ForeignKey(
            'artist.mbid',
            onupdate="CASCADE",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED"),
        nullable=True)
    activity = Column(Enum(ActivityTypes))
    data = Column(JSON)

    user = relationship(User, lazy=True, uselist=False)
    release = relationship("Release", lazy=True, uselist=False)
    artist = relationship("Artist", lazy=True, uselist=False)

    def __repr__(self):
        return '<UserActivity {}>'.format(self.id)


artist_release = db.Table(
    'artist_release',
    Column(
        'artist_mbid',
        String(36),
        ForeignKey(
            'artist.mbid',
            onupdate="CASCADE",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED"),
        primary_key=True),
    Column(
        'release_mbid',
        String(36),
        ForeignKey(
            'release.mbid',
            onupdate="CASCADE",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED"),
        primary_key=True)
)


class Artist(db.Model):
    mbid = Column(
        String(36),
        primary_key=True)
    name = Column(
        String(512),
        nullable=False)
    active = Column(
        Boolean(),
        server_default=expression.true(),
        default=True)
    sort_name = Column(
        String(512),
        nullable=False)
    disambiguation = Column(
        String(512),
        nullable=False)
    art = Column(
        String(100),
        nullable=True,
        server_default=expression.null(),
        default=None)
    date_added = Column(
        DateTime(True),
        nullable=False,
        server_default=func.now(),
        default=func.now())
    date_art_check = Column(
        DateTime(True),
        nullable=True,
        server_default=expression.null(),
        default=None)
    date_updated = Column(
        DateTime(True),
        nullable=True,
        server_default=expression.null(),
        default=None)
    apple_music_link = Column(
        String(),
        nullable=True)
    spotify_link = Column(
        String(),
        nullable=True)

    users = relationship("User", secondary="user_artist", lazy=True)
    akas = relationship("ArtistAka", lazy=False)
    releases = relationship("Release", secondary=artist_release, lazy=True)

    def __repr__(self):
        return '<Artist {} - {}>'.format(self.name, self.mbid)


class ArtistAka(db.Model):
    artist_mbid = Column(
        String(36),
        ForeignKey(
            'artist.mbid',
            onupdate="CASCADE",
            ondelete="CASCADE"),
        index=True,
        primary_key=True)
    name = Column(
        String(512),
        nullable=False,
        primary_key=True)

    def __repr__(self):
        return '<ArtistAka {} - {}>'.format(self.artist_mbid, self.name)


class UserArtist(db.Model):
    user_id = Column(
        Integer,
        ForeignKey(
            'user.id',
            onupdate="CASCADE",
            ondelete="CASCADE"),
        primary_key=True)

    mbid = Column(
        String(36),
        ForeignKey(
            'artist.mbid',
            onupdate="CASCADE",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED"),
        primary_key=True)
    name = Column(
        String(512),
        nullable=False)
    sort_name = Column(
        String(512),
        nullable=False)
    disambiguation = Column(
        String(512),
        nullable=False)
    art = Column(
        String(100),
        nullable=True,
        server_default=expression.null(),
        default=None)
    date_updated = Column(
        DateTime(True),
        nullable=True,
        server_default=expression.null(),
        default=None)
    apple_music_link = Column(
        String(),
        nullable=True)
    spotify_link = Column(
        String(),
        nullable=True)

    date_followed = Column(
        DateTime(True),
        nullable=False,
        server_default=func.now(),
        default=func.now())
    follow_method = Column(
        Enum(ImportMethod))
    following = Column(
        Boolean(),
        server_default=expression.false(),
        default=True,
        index=True)

    user = relationship(User, lazy=True, uselist=False)

    def __repr__(self):
        return '<UserArtist {} - {}>'.format(self.user_id, self.mbid)


class Release(db.Model):
    mbid = Column(
        String(36),
        primary_key=True)
    title = Column(
        String(512),
        nullable=False)
    artists_string = Column(
        String(512),
        nullable=False)
    active = Column(
        Boolean(),
        server_default=expression.true(),
        default=True)
    type = Column(
        Enum(ReleaseType),
        index=True)
    date_release = Column(
        db.Date,
        nullable=False,
        index=True,
        server_default=expression.null(),
        default=None)
    art = Column(
        String(100),
        nullable=True,
        server_default=expression.null(),
        default=None)
    date_added = Column(
        DateTime(True),
        nullable=False,
        server_default=func.now(),
        default=func.now())
    date_art_check = Column(
        DateTime(True),
        nullable=True,
        server_default=expression.null(),
        default=None)
    date_updated = Column(
        DateTime(True),
        nullable=False,
        server_default=func.now(),
        default=func.now())
    apple_music_link = Column(
        String(),
        nullable=True)
    spotify_link = Column(
        String(),
        nullable=True)

    artists = db.relationship('Artist', secondary=artist_release, lazy=False)

    def __repr__(self):
        return '<Release {} - {} - {}>'.format(
            self.artists_string,
            self.title,
            self.mbid)


class UserRelease(db.Model):
    user_id = Column(
        Integer,
        ForeignKey(
            'user.id',
            onupdate="CASCADE",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED"),
        index=True,
        primary_key=True)

    mbid = Column(
        String(36),
        ForeignKey(
            'release.mbid',
            onupdate="CASCADE",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED"),
        primary_key=True)
    title = Column(
        String(512),
        nullable=False)
    artists_string = Column(
        String(512),
        nullable=False)
    type = Column(
        Enum(ReleaseType),
        index=True)
    date_release = Column(
        db.Date,
        nullable=False,
        index=True,
        server_default=expression.null(),
        default=None)
    art = Column(
        String(100),
        nullable=True,
        server_default=expression.null(),
        default=None)
    date_updated = Column(
        DateTime(True),
        nullable=False,
        server_default=func.now(),
        default=func.now())
    apple_music_link = Column(
        String(),
        nullable=True)
    spotify_link = Column(
        String(),
        nullable=True)

    date_added = Column(
        DateTime(True),
        nullable=False,
        server_default=func.now(),
        default=func.now())
    add_method = Column(
        Enum(AddMethod))

    listened = Column(
        Boolean(),
        server_default=expression.false(),
        default=False)
    date_listened = Column(
        DateTime(True),
        nullable=True,
        index=True)

    def __repr__(self):
        return '<UserRelease {} - {}>'.format(
            self.user_id,
            self.mbid)


class ArtistImport(db.Model):
    user_id = Column(
        Integer,
        ForeignKey(
            'user.id',
            onupdate="CASCADE",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED"),
        index=True,
        primary_key=True)
    import_name = Column(
        String(100),
        primary_key=True)
    import_mbid = Column(
        String(36),
        nullable=True)
    import_method = Column(
        Enum(ImportMethod))
    found_mbid = Column(
        String(36),
        ForeignKey(
            'artist.mbid',
            onupdate="CASCADE",
            ondelete="SET NULL",
            deferrable=True,
            initially="DEFERRED"),
        nullable=True)
    date_added = Column(
        DateTime(True),
        nullable=False,
        server_default=func.now(),
        default=func.now())
    date_checked = Column(
        DateTime(True),
        nullable=True,
        server_default=expression.null(),
        default=None)

    def __repr__(self):
        return '<ArtistImport {} - {}>'.format(
            self.user_id,
            self.import_name)


class UserNotifications(db.Model):
    user_id = Column(
        Integer,
        ForeignKey(
            'user.id',
            onupdate="CASCADE",
            ondelete="CASCADE"),
        primary_key=True)
    date_created = Column(
        DateTime(True),
        index=True,
        nullable=False,
        server_default=func.now(),
        default=func.now())
    type = Column(
        Enum(NotificationType),
        index=True)
    release_mbid = Column(
        String(36),
        ForeignKey(
            'release.mbid',
            onupdate="CASCADE",
            ondelete="CASCADE",
            deferrable=True,
            initially="DEFERRED"),
        primary_key=True)
    date_sent = Column(
        DateTime(True),
        nullable=True,
        server_default=expression.null(),
        default=None)

    release = relationship(Release, lazy=False, uselist=False)
