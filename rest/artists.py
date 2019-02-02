from flask import g, jsonify, request
from datetime import date

import response
from backend.serializer import serializer
from backend.models import UserArtist
from numu import app as numu_app
from numu import auth

from . import app

PER_PAGE = 50


def paginate_query(query, page):
    paginated = query.paginate(page=page, per_page=PER_PAGE, error_out=True)
    return {
        "page": page,
        "per_page": PER_PAGE,
        "total_pages": paginated.pages,
        "next_page": paginated.next_num,
        "prev_page": paginated.prev_num,
        "items": [serializer(item, "user_artist") for item in paginated.items],
    }


"""
@app.route('/user/artist/<mbid>', methods=['GET'])
@auth.login_required
def user_artist_by_mbid():
    return user_artists(1)
"""


@app.route("/user/artists", methods=["GET"])
@auth.login_required
def user_artists_no_page():
    return user_artists(1)


@app.route("/user/artists/<int:page>", methods=["GET"])
@auth.login_required
def user_artists(page):
    query = UserArtist.query.filter(UserArtist.user_id == g.user.id)
    data = paginate_query(query, page)
    return response.success(data)
