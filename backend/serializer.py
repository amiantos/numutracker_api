"""Serialize models for API return."""
from backend.models import Artist, Release, UserRelease


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


def user_releases(user_releases):
    serialized = []
    for release in user_releases:
        r = {
            'mbid': release.mbid,
            'title': release.title,
            'artist_names': release.artist_names,
            'type': release.type,
            'art': get_art_urls(release),
            'date_release': release.date_release,
            'date_updated': release.date_updated,
            'links': {
                'apple_music': release.apple_music_link,
                'spotify': release.spotify_link,
            },
            'listened': release.listened,
            'date_listened': release.date_listened,
            'artists': [artist(x) for x in release.release.artists]
        }
        serialized.append(r)
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
