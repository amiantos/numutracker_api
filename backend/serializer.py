"""Serialize models for API return."""
from backend.models import Artist, Release, UserRelease, ArtistRelease
from numu import db, app as numu_app
from backend import repo
from sqlalchemy.orm import joinedload
import json


def serializer(object, type):
    if type == "user_release":
        return user_releases(object)
    if type == "user_artist":
        return user_artist_serializer(object)
    if type == "artist_release_with_user":
        return artist_release_with_user(object)


def get_art_urls(object):
    """Creates URLs for artist or release art."""
    if object.art is False and type(object) is Release:
        for artist in object.artists:
            if artist.art is True:
                return {
                    "thumbUrl": "https://numu.sfo2.digitaloceanspaces.com/artist/thumb/{}.png".format(
                        artist.mbid
                    ),
                    "fullUrl": "https://numu.sfo2.digitaloceanspaces.com/artist/full/{}.png".format(
                        artist.mbid
                    ),
                    "largeUrl": "https://numu.sfo2.digitaloceanspaces.com/artist/large/{}.png".format(
                        artist.mbid
                    ),
                }
    if object.art is False:
        return None
    if type(object) is Release:
        return {
            "thumbUrl": "https://numu.sfo2.digitaloceanspaces.com/release/thumb/{}.png".format(
                object.mbid
            ),
            "fullUrl": "https://numu.sfo2.digitaloceanspaces.com/release/full/{}.png".format(
                object.mbid
            ),
            "largeUrl": "https://numu.sfo2.digitaloceanspaces.com/release/large/{}.png".format(
                object.mbid
            ),
        }
    if type(object) is Artist:
        return {
            "thumbUrl": "https://numu.sfo2.digitaloceanspaces.com/artist/thumb/{}.png".format(
                object.mbid
            ),
            "fullUrl": "https://numu.sfo2.digitaloceanspaces.com/artist/full/{}.png".format(
                object.mbid
            ),
            "largeUrl": "https://numu.sfo2.digitaloceanspaces.com/artist/large/{}.png".format(
                object.mbid
            ),
        }


def artist_release_with_user(tuple):
    release = tuple[1]
    user_release = tuple[2]

    serialized = {
        "mbid": release.mbid,
        "title": release.title,
        "artistNames": release.artist_names,
        "type": release.type,
        "art": get_art_urls(release),
        "dateRelease": release.date_release,
        "dateAdded": release.date_added,
        "dateUpdated": release.date_updated,
        "links": {
            "appleMusic": release.apple_music_link,
            "spotify": release.spotify_link,
        },
        "artists": [artist(x) for x in release.artists],
        "userData": None,
    }
    if user_release:
        serialized["userData"] = {
            "uuid": user_release.uuid,
            "listened": user_release.listened,
            "following": user_release.following,
            "dateListened": user_release.date_listened,
            "dateFollowed": user_release.date_followed,
            "dateUpdated": user_release.date_updated,
        }
    return serialized


def user_releases(user_release):
    serialized = {
        "mbid": user_release.mbid,
        "title": user_release.title,
        "artistNames": user_release.artist_names,
        "type": user_release.type,
        "art": get_art_urls(user_release.release),
        "dateRelease": user_release.date_release,
        "dateAdded": user_release.release.date_added,
        "dateUpdated": user_release.release.date_updated,
        "links": {
            "appleMusic": user_release.apple_music_link,
            "spotify": user_release.spotify_link,
        },
        "artists": [artist(x) for x in user_release.release.artists],
        "userData": {
            "uuid": user_release.uuid,
            "listened": user_release.listened,
            "following": user_release.following,
            "dateListened": user_release.date_listened,
            "dateFollowed": user_release.date_followed,
            "dateUpdated": user_release.date_updated,
        },
    }
    return serialized


def user_artist_serializer(user_artist):
    recent_release = (
        Release.query.filter(
            Release.mbid.in_(
                db.session.query(ArtistRelease.release_mbid)
                .filter(ArtistRelease.artist_mbid == user_artist.mbid)
                .all()
            ),
            Release.type.in_(user_artist.user.filters),
        )
        .order_by(Release.date_release.desc())
        .limit(1)
        .first()
    )
    recent_release_date = recent_release.date_release if recent_release else None
    serialized = {
        "mbid": user_artist.mbid,
        "name": user_artist.artist.name,
        "sortName": user_artist.artist.sort_name,
        "disambiguation": user_artist.artist.disambiguation,
        "art": get_art_urls(user_artist.artist),
        "dateUpdated": user_artist.artist.date_updated,
        "recentReleaseDate": recent_release_date,
        "userData": {
            "uuid": user_artist.uuid,
            "following": user_artist.following,
            "dateFollowed": user_artist.date_followed,
            "dateUpdated": user_artist.date_updated,
        },
    }
    return serialized


def artist(artist):
    return {
        "mbid": artist.mbid,
        "name": artist.name,
        "sortName": artist.sort_name,
        "disambiguation": artist.disambiguation,
        "art": get_art_urls(artist),
        "dateUpdated": artist.date_updated,
    }
