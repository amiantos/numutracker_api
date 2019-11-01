import musicbrainzngs as mbz


mbz.set_useragent(
    "numutracker_api", "3.0", "https://github.com/amiantos/numutracker_api"
)

blacklisted_artists = {
    "89ad4ac3-39f7-470e-963a-56509c546377",  # Various Artists
    "fe5b7087-438f-4e7e-afaf-6d93c8c888b2",
    "0677ef60-6be5-4e36-9d1e-8bb2bf85b981",
    "b7c7dfd9-d735-4733-9b10-f060ac75bd6a",
    "b05cc773-4e8e-40bc-ae12-dc88dfc2c9ec",
    "4b2228f5-e18b-4acc-ace7-b8db13a9306f",
    "046c889d-5b1c-4f54-9c7b-319a8f67e729",
    "1bf34db2-8447-4ecd-9b25-57945b28ef28",
    "023671ff-b1ad-4133-a4f3-aadaaadfd2e0",
    "f731ccc4-e22a-43af-a747-64213329e088",  # [anonymous]
    "33cf029c-63b0-41a0-9855-be2a3665fb3b",  # [data]
    "314e1c25-dde7-4e4d-b2f4-0a7b9f7c56dc",  # [dialogue]
    "eec63d3c-3b81-4ad4-b1e4-7c147d4d2b61",  # [no artist]
    "9be7f096-97ec-4615-8957-8d40b5dcbc41",  # [traditional]
    "125ec42a-7229-4250-afc5-e057484327fe",  # [unknown]
    "203b6058-2401-4bf0-89e3-8dc3d37c3f12",
    "5e760f5a-ea55-4b53-a18f-021c0d9779a6",
    "1d8bc797-ec8a-40d2-8d80-b1346b56a65f",
    "7734d67f-44d9-4ba2-91e3-9b067263210e",
    "f49cc9f4-dc00-48ab-9aab-6387c02738cf",
    "0035056d-72ac-41fa-8ea6-0e27e55f42f7",
    "d6bd72bc-b1e2-4525-92aa-0f853cbb41bf",  # [soundtrack]
    "702245c5-dd3e-4ecd-bf7f-6cae5341cd29",  # [archive]
}


def search_artist_by_name(name):
    try:
        result = mbz.search_artists(
            query="artist:{}".format(name.replace("/", " ")), limit=10, strict=True
        )
    except mbz.ResponseError as err:
        status = err.cause.code
        result = None
    else:
        status = 200
        result = result["artist-list"]

    for artist in result:
        if artist["id"] not in blacklisted_artists:
            return {"status": status, "artist": artist}

    return {"status": status, "artist": None}


def get_artist(artist_mbid):
    result = None
    try:
        result = mbz.get_artist_by_id(artist_mbid)
    except mbz.ResponseError as err:
        print(err)
        status = err.cause.code
    else:
        status = 404
        if result["artist"]["id"] not in blacklisted_artists:
            status = 200
            result = result["artist"]

    return {"status": status, "artist": result}


def get_release(release_mbid):
    try:
        result = mbz.get_release_group_by_id(release_mbid, includes=["artist-credits"])
    except mbz.ResponseError as err:
        status = err.cause.code
        result = None
    else:
        status = 200
        result = result["release-group"]

    return {"status": status, "release": result}


def get_artist_releases(artist_mbid):
    limit = 100
    offset = 0
    releases = []
    release_groups = []
    page = 1

    result = mbz.browse_releases(
        artist=artist_mbid,
        limit=limit,
        offset=offset,
        includes=["release-groups", "artist-credits"],
        release_status=["official"],
    )

    releases += result["release-list"]

    if "release-count" in result:
        count = result["release-count"]

        while len(releases) < count:
            offset += limit
            page += 1

            result = mbz.browse_releases(
                artist=artist_mbid,
                limit=limit,
                offset=offset,
                includes=["release-groups", "artist-credits"],
                release_status=["official"],
            )
            releases += result["release-list"]

    for release in releases:
        if release not in release_groups:
            release_groups.append(release["release-group"])

    return {"status": 200, "releases": release_groups}

