"""Serialize models for API return."""
from backend.models import Artist, Release, UserRelease


def serializer(object, type):
    if type == 'user_release':
        return user_releases(object)


def get_art_urls(object):
    """Creates URLs for artist or release art."""
    if object.art is False:
        return None
    if type(object) is UserRelease:
        return {
            'thumb': 'https://numu.sfo2.digitaloceanspaces.com/release/thumb/{}.png'.format(object.mbid),
            'full': 'https://numu.sfo2.digitaloceanspaces.com/release/full/{}.png'.format(object.mbid),
            'large': 'https://numu.sfo2.digitaloceanspaces.com/release/large/{}.png'.format(object.mbid)
        }
    if type(object) is Artist:
        return {
            'thumb': 'https://numu.sfo2.digitaloceanspaces.com/artist/thumb/{}.png'.format(object.mbid),
            'full': 'https://numu.sfo2.digitaloceanspaces.com/artist/full/{}.png'.format(object.mbid),
            'large': 'https://numu.sfo2.digitaloceanspaces.com/artist/large/{}.png'.format(object.mbid)
        }


def user_releases(user_release):
    serialized = {
        'mbid': user_release.mbid,
        'title': user_release.title,
        'artist_names': user_release.artist_names,
        'type': user_release.type,
        'art': get_art_urls(user_release),
        'date_release': user_release.date_release,
        'date_updated': user_release.date_updated,
        'links': {
            'apple_music': user_release.apple_music_link,
            'spotify': user_release.spotify_link,
        },
        'listened': user_release.listened,
        'date_listened': user_release.date_listened,
        'artists': [artist(x) for x in user_release.release.artists]
    }
    return serialized


def artist(artist):
    return {
        'mbid': artist.mbid,
        'name': artist.name,
        'sort_name': artist.sort_name,
        'disambiguation': artist.disambiguation,
        'art': get_art_urls(artist),
        'date_updated': artist.date_updated,
    }
