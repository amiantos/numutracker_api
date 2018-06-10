import enum

from sqlalchemy.sql import expression, func
from sqlalchemy.orm import relationship, backref

from main import app
from main import db

from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)


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


class FollowMethod(enum.Enum):
    APPLE = "Apple Music"
    SPOTIFY = "Spotify"


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


class User(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True)
    email = db.Column(
        db.String(120),
        index=True,
        unique=True)
    password_hash = db.Column(
        db.String(128))
    username = db.Column(
        db.String(12),
        nullable=True,
        unique=True)
    date_joined = db.Column(
        db.DateTime(True),
        server_default=func.now(),
        default=func.now())
    album = db.Column(
        db.Boolean(),
        server_default=expression.true(),
        default=True)
    single = db.Column(
        db.Boolean(),
        server_default=expression.true(),
        default=True)
    ep = db.Column(
        db.Boolean(),
        server_default=expression.true(),
        default=True)
    live = db.Column(
        db.Boolean(),
        server_default=expression.false(),
        default=False)
    soundtrack = db.Column(
        db.Boolean(),
        server_default=expression.false(),
        default=False)
    remix = db.Column(
        db.Boolean(),
        server_default=expression.false(),
        default=False)
    other = db.Column(
        db.Boolean(),
        server_default=expression.false(),
        default=False)

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
    id = db.Column(
        db.Integer,
        primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'))
    date = db.Column(
        db.DateTime(True),
        server_default=func.now(),
        default=func.now())
    release_mbid = db.Column(
        db.String(36),
        db.ForeignKey('release.mbid'),
        nullable=True)
    artist_mbid = db.Column(
        db.String(36),
        db.ForeignKey('artist.mbid'),
        nullable=True)
    activity = db.Column(db.Enum(ActivityTypes))

    user = relationship(User, lazy=True)

    def __repr__(self):
        return '<UserActivity {}>'.format(self.id)


artist_release = db.Table(
    'artist_release',
    db.Column(
        'artist_mbid',
        db.String(36),
        db.ForeignKey('artist.mbid'),
        primary_key=True),
    db.Column(
        'release_mbid',
        db.String(36),
        db.ForeignKey('release.mbid'),
        primary_key=True)
)


class Artist(db.Model):
    mbid = db.Column(
        db.String(36),
        primary_key=True)
    name = db.Column(
        db.String(512),
        nullable=False)
    sort_name = db.Column(
        db.String(512),
        nullable=False)
    disambiguation = db.Column(
        db.String(512),
        nullable=False)
    art = db.Column(
        db.String(100),
        nullable=True,
        server_default=expression.null(),
        default=None)
    date_added = db.Column(
        db.DateTime(True),
        nullable=False,
        server_default=func.now(),
        default=func.now())
    date_art_check = db.Column(
        db.DateTime(True),
        nullable=True,
        server_default=expression.null(),
        default=None)
    date_updated = db.Column(
        db.DateTime(True),
        nullable=False,
        server_default=func.now(),
        default=func.now())

    followers = relationship("User", secondary="user_artist", lazy=True)
    aka = relationship("ArtistAka", lazy=False)
    releases = relationship("Release", lazy=True)

    def __repr__(self):
        return '<Artist {} - {}>'.format(self.name, self.mbid)


class ArtistAka(db.Model):
    artist_mbid = db.Column(
        db.String(36),
        db.ForeignKey('artist.mbid'),
        index=True,
        primary_key=True)
    name = db.Column(
        db.String(512),
        nullable=False,
        primary_key=True)

    def __repr__(self):
        return '<ArtistAka {} - {}>'.format(self.artist_mbid, self.name)


class UserArtist(db.Model):
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        primary_key=True)
    artist_mbid = db.Column(
        db.String(36),
        db.ForeignKey('artist.mbid'),
        primary_key=True)
    date_followed = db.Column(
        db.DateTime(True),
        nullable=False,
        server_default=func.now(),
        default=func.now())
    follow_method = db.Column(
        db.Enum(FollowMethod))

    user = relationship(User, lazy=True)
    artist = relationship(Artist, secondary=artist_release, lazy=False)

    def __repr__(self):
        return '<UserArtist {} - {}>'.format(self.user_id, self.artist_mbid)


class Release(db.Model):
    mbid = db.Column(
        db.String(36),
        primary_key=True)
    title = db.Column(
        db.String(512),
        nullable=False)
    artists_string = db.Column(
        db.String(512),
        nullable=False)
    type = db.Column(
        db.Enum(ReleaseType),
        index=True)
    date_release = db.Column(
        db.Date,
        nullable=False,
        index=True,
        server_default=expression.null(),
        default=None)
    art = db.Column(
        db.String(100),
        nullable=True,
        server_default=expression.null(),
        default=None)
    date_added = db.Column(
        db.DateTime(True),
        nullable=False,
        server_default=func.now(),
        default=func.now())
    date_art_check = db.Column(
        db.DateTime(True),
        nullable=True,
        server_default=expression.null(),
        default=None)
    date_updated = db.Column(
        db.DateTime(True),
        nullable=False,
        server_default=func.now(),
        default=func.now())

    artists = db.relationship('Artist', secondary=artist_release, lazy=True)

    def __repr__(self):
        return '<Release {} - {} - {}>'.format(
            self.artists_string,
            self.title,
            self.mbid)


class UserRelease(db.Model):
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        index=True,
        primary_key=True)
    release_mbid = db.Column(
        db.String(36),
        db.ForeignKey('release.mbid'),
        primary_key=True)
    date_added = db.Column(
        db.DateTime(True),
        nullable=False,
        server_default=func.now(),
        default=func.now())
    add_method = db.Column(
        db.Enum(AddMethod))
    date_listened = db.Column(
        db.DateTime(True),
        nullable=True)

    release = relationship(Release, lazy='joined')

    def __repr__(self):
        return '<UserRelease {} - {}>'.format(
            self.user_id,
            self.mbid)


class ArtistImport(db.Model):
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        index=True,
        primary_key=True)
    name = db.Column(
        db.String(100),
        primary_key=True)
    artist_mbid = db.Column(
        db.String(36),
        db.ForeignKey('artist.mbid'),
        nullable=True)
    date_added = db.Column(
        db.DateTime(True),
        nullable=False,
        server_default=func.now(),
        default=func.now())
    date_checked = db.Column(
        db.DateTime(True),
        nullable=True,
        server_default=expression.null(),
        default=None)

    def __repr__(self):
        return '<ArtistImport {} - {}>'.format(
            self.user_id,
            self.name)


class UserNotifications(db.Model):
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        primary_key=True)
    date_created = db.Column(
        db.DateTime(True),
        index=True,
        nullable=False,
        server_default=func.now(),
        default=func.now())
    type = db.Column(
        db.Enum(NotificationType),
        index=True)
    release_mbid = db.Column(
        db.String(36),
        db.ForeignKey('release.mbid'),
        primary_key=True)
    date_sent = db.Column(
        db.DateTime(True),
        nullable=True,
        server_default=expression.null(),
        default=None)

    release = relationship(Release, lazy=False)