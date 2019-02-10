from flask import g

import response
from backend.models import ArtistRelease, Release, UserArtist, UserRelease
from backend.serializer import serializer
from numu import auth, db

from . import app

PER_PAGE = 10000


def paginate_query(query, offset, type):
    total_results = query.count()
    results = query.limit(PER_PAGE).offset(offset)
    result_count = results.count()
    return {
        "offset": offset,
        "resultsPerRequest": PER_PAGE,
        "totalResults": total_results,
        "resultsRemaining": total_results - offset - result_count,
        "userArtists": [serializer(item, type) for item in results],
    }


@app.route("/user/artists", methods=["GET"])
@auth.login_required
def user_artists_no_offset():
    return user_artists(0)


@app.route("/user/artists/<int:offset>", methods=["GET"])
@auth.login_required
def user_artists(offset):
    query = UserArtist.query.filter(UserArtist.user_id == g.user.id).order_by(
        UserArtist.name
    )
    data = paginate_query(query, offset, "user_artist")
    return response.success(data)
