import musicbrainzngs as mbz

from main import db
from models import ArtistImport, Artist, Release, ReleaseType

mbz.set_useragent(
    "numutracker_api",
    "3.0",
    "https://github.com/amiantos/numutracker_api",
)

def get_artist(mbid):
    try:
        result = mbz.get_artist_by_id(mbid)
    except mbz.ResponseError as err:
        status = err.cause.code
        result = None
    else:
        status = 200
        result = result["artist"]

    return {'status': status, 'result': result}
