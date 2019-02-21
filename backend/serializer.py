"""Serialize models for API return."""
from backend.models import Artist, Release, DeletedArtist, DeletedRelease


def serializer(object, type):
    if type == "user_release_quick":
        return user_releases_quick(object)
    if type == "user_release":
        return user_release(object)
    if type == "user_artist":
        return user_artist(object)
    if type == "deletion":
        return deletion(object)


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


def user_releases_quick(tuple):
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
        serialized["userData"] = {
            "listened": user_release.listened,
            "following": user_release.following,
            "dateListened": user_release.date_listened,
            "dateFollowed": user_release.date_followed,
            "dateUpdated": user_release.date_updated,
        }
    return serialized


def user_release(user_release):
    serialized = {
        "mbid": user_release.release.mbid,
        "title": user_release.release.title,
        "artistNames": user_release.release.artist_names,
        "type": user_release.release.type,
        "art": get_art_urls(user_release.release),
        "dateRelease": user_release.release.date_release,
        "dateAdded": user_release.release.date_added,
        "dateUpdated": user_release.release.date_updated,
        "links": user_release.release.links,
        "artists": [artist(x) for x in user_release.release.artists],
        "userData": {
            "listened": user_release.listened,
            "following": user_release.following,
            "dateListened": user_release.date_listened,
            "dateFollowed": user_release.date_followed,
            "dateUpdated": user_release.date_updated,
        },
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


def deletion(object):
    if type(object) is DeletedArtist:
        return {"deletedArtist": deletion_data(object)}
    if type(object) is DeletedRelease:
        return {"deletedRelease": deletion_data(object)}


def deletion_data(object):
    return {
        "mbid": object.mbid,
        "date_deleted": object.date_deleted,
        "meta": object.meta,
    }
