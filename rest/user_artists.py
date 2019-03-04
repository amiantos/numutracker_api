from datetime import datetime
from flask import g, request

import response
from .api_key import require_apikey
from backend.models import UserArtist, Artist
from backend.serializer import serializer
from numu import auth
from sqlalchemy import or_

from . import app

PER_PAGE = 50


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
@require_apikey
def user_artists():
    try:
        offset = int(request.args.get("offset", 0))
        date_offset = int(request.args.get("date_offset", 0))
    except ValueError:
        offset = 0
        date_offset = None

    if date_offset is not None:
        try:
            date_offset = datetime.fromtimestamp(date_offset)
        except TypeError:
            date_offset = None

    if date_offset:
        query = (
            UserArtist.query.join(Artist)
            .filter(
                UserArtist.user_id == g.user.id,
                or_(
                    UserArtist.date_updated >= date_offset,
                    Artist.date_updated == date_offset,
                ),
            )
            .order_by(UserArtist.date_updated.desc())
        )
    else:
        query = UserArtist.query.filter(UserArtist.user_id == g.user.id).order_by(
            UserArtist.date_updated.desc()
        )
    data = paginate_query(query, offset, "user_artist")
    return response.success(data)
