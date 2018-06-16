import musicbrainzngs as mbz


mbz.set_useragent(
    "numutracker_api",
    "3.0",
    "https://github.com/amiantos/numutracker_api",
)


def get_artist(artist_mbid):
    try:
        result = mbz.get_artist_by_id(artist_mbid)
    except mbz.ResponseError as err:
        status = err.cause.code
        result = None
    else:
        status = 200
        result = result["artist"]

    return {'status': status, 'result': result}


def get_release(release_mbid):
    try:
        result = mbz.get_release_group_by_id(release_mbid)
    except mbz.ResponseError as err:
        status = err.cause.code
        result = None
    else:
        status = 200
        result = result["release-group"]

    return {'status': status, 'result': result}


def get_artist_releases(artist_mbid):
    limit = 100
    offset = 0
    releases = []
    page = 1

    result = mbz.browse_release_groups(artist=artist_mbid, limit=limit, offset=offset)
    releases += result['release-group-list']

    if 'release-group-count' in result:
        count = result['release-group-count']
    
    while len(releases) < count:
        offset += limit
        page += 1

        result = mbz.browse_release_groups(artist=artist_mbid, limit=limit, offset=offset)
        releases += result['release-group-list']
    
    return {'status': 200, 'result': releases}
    