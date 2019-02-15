from flask import g, request

import response
from backend.models import UserArtist
from backend.serializer import serializer
from numu import auth

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
def user_artists():
    try:
        offset = int(request.args.get("offset", 0))
    except ValueError:
        offset = 0
    query = UserArtist.query.filter(UserArtist.user_id == g.user.id).order_by(
        UserArtist.date_updated.desc()
    )
    data = paginate_query(query, offset, "user_artist")
    return response.success(data)
