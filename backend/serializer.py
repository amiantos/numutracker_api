"""Serialize models for API return."""
from backend.models import Artist, Release


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


def user_releases(tuple):
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
        "links": release.links,
        "artists": [artist(x) for x in release.artists],
        "userData": None,
    }
    if user_release:
        serialized["user_data"] = {
            "uuid": user_release.uuid,
            "listened": user_release.listened,
            "following": user_release.following,
            "dateListened": user_release.date_listened,
            "dateFollowed": user_release.date_followed,
            "dateUpdated": user_release.date_updated,
        }
    return serialized


def user_artist(user_artist):
    serialized = {
        "mbid": user_artist.mbid,
        "name": user_artist.artist.name,
        "sortName": user_artist.artist.sort_name,
        "disambiguation": user_artist.artist.disambiguation,
        "art": get_art_urls(user_artist.artist),
        "dateUpdated": user_artist.artist.date_updated,
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
