from flask import g

import response
from backend.models import ArtistRelease, Release, UserArtist, UserRelease
from backend.serializer import serializer
from numu import auth, db
from sqlalchemy.orm import aliased

from . import app

PER_PAGE = 50


def paginate_query(query, page, type):
    paginated = query.paginate(page=page, per_page=PER_PAGE, error_out=True)
    return {
        "page": page,
        "perPage": PER_PAGE,
        "totalPages": paginated.pages,
        "nextPage": paginated.next_num,
        "prevPage": paginated.prev_num,
        "userArtists": [serializer(item, type) for item in paginated.items],
    }


@app.route("/user/artists", methods=["GET"])
@auth.login_required
def user_artists_no_page():
    return user_artists(1)


@app.route("/user/artists/<int:page>", methods=["GET"])
@auth.login_required
def user_artists(page):
    query = UserArtist.query.filter(UserArtist.user_id == g.user.id).order_by(
        UserArtist.name
    )
    data = paginate_query(query, page, "user_artist")
    return response.success(data)


@app.route("/user/artist/<string:mbid>/releases", methods=["GET"])
@auth.login_required
def user_artist_releases_no_page(mbid):
    return user_artist_releases(mbid, 1)


@app.route("/user/artist/<string:mbid>/releases/<int:page>", methods=["GET"])
@auth.login_required
def user_artist_releases(mbid, page):
    query = (
        db.session.query(ArtistRelease, Release, UserRelease)
        .join(Release)
        .outerjoin(UserRelease)
        .filter(ArtistRelease.artist_mbid == mbid, Release.type.in_(g.user.filters))
        .order_by(Release.date_release.desc())
    )
    data = paginate_query(query, page, "artist_release_with_user")
    return response.success(data)
