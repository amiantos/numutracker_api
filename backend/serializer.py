"""Serialize models for API return."""
from backend.models import Artist, Release, UserRelease, ArtistRelease
from numu import db
from backend import repo
from sqlalchemy.orm import joinedload


def serializer(object, type):
    if type == "user_release":
        return user_releases(object)
    if type == "user_artist":
        return user_artist(object)


def get_art_urls(object):
    """Creates URLs for artist or release art."""
    if object.art is False and type(object) is Release:
        for artist in object.artists:
            if artist.art is True:
                return {
                    "thumb": "https://numu.sfo2.digitaloceanspaces.com/artist/thumb/{}.png".format(
                        artist.mbid
                    ),
                    "full": "https://numu.sfo2.digitaloceanspaces.com/artist/full/{}.png".format(
                        artist.mbid
                    ),
                    "large": "https://numu.sfo2.digitaloceanspaces.com/artist/large/{}.png".format(
                        artist.mbid
                    ),
                }
    if object.art is False:
        return None
    if type(object) is Release:
        return {
            "thumb": "https://numu.sfo2.digitaloceanspaces.com/release/thumb/{}.png".format(
                object.mbid
            ),
            "full": "https://numu.sfo2.digitaloceanspaces.com/release/full/{}.png".format(
                object.mbid
            ),
            "large": "https://numu.sfo2.digitaloceanspaces.com/release/large/{}.png".format(
                object.mbid
            ),
        }
    if type(object) is Artist:
        return {
            "thumb": "https://numu.sfo2.digitaloceanspaces.com/artist/thumb/{}.png".format(
                object.mbid
            ),
            "full": "https://numu.sfo2.digitaloceanspaces.com/artist/full/{}.png".format(
                object.mbid
            ),
            "large": "https://numu.sfo2.digitaloceanspaces.com/artist/large/{}.png".format(
                object.mbid
            ),
        }


def user_releases(user_release):
    serialized = {
        "mbid": user_release.mbid,
        "title": user_release.title,
        "artist_names": user_release.artist_names,
        "type": user_release.type,
        "art": get_art_urls(user_release.release),
        "date_release": user_release.date_release,
        "date_added": user_release.date_added,
        "date_updated": user_release.release.date_updated,
        "links": {
            "apple_music": user_release.apple_music_link,
            "spotify": user_release.spotify_link,
        },
        "artists": [artist(x) for x in user_release.release.artists],
        "user_data": {
            "listened": user_release.listened,
            "date_listened": user_release.date_listened,
            "date_added": user_release.date_added,
            "date_updated": user_release.date_updated,
        },
    }
    return serialized


def user_artist(user_artist):
    total_releases = Release.query.filter(
        Release.mbid.in_(
            db.session.query(ArtistRelease.release_mbid)
            .filter(ArtistRelease.artist_mbid == user_artist.mbid)
            .all()
        ),
        Release.type.in_(user_artist.user.filters),
    ).count()
    listened_releases = UserRelease.query.filter(
        UserRelease.mbid.in_(
            db.session.query(ArtistRelease.release_mbid)
            .filter(ArtistRelease.artist_mbid == user_artist.mbid)
            .all()
        ),
        UserRelease.listened.is_(True),
        UserRelease.type.in_(user_artist.user.filters),
    ).count()
    serialized = {
        "mbid": user_artist.mbid,
        "name": user_artist.artist.name,
        "sort_name": user_artist.artist.sort_name,
        "disambiguation": user_artist.artist.disambiguation,
        "art": get_art_urls(user_artist.artist),
        "date_updated": user_artist.artist.date_updated,
        "user_data": {
            "following": user_artist.following,
            "date_followed": user_artist.date_followed,
            "date_updated": user_artist.date_updated,
            "total_releases": total_releases,
            "listened_releases": listened_releases,
        },
    }
    return serialized


def artist(artist):
    return {
        "mbid": artist.mbid,
        "name": artist.name,
        "sort_name": artist.sort_name,
        "disambiguation": artist.disambiguation,
        "art": get_art_urls(artist),
        "date_updated": artist.date_updated,
    }
