from datetime import datetime

from flask import g, request

import response
from .api_key import require_apikey
from backend.models import UserRelease, Release, ArtistRelease, UserArtist
from backend.serializer import serializer
from numu import auth, db, app as numu_app
from sqlalchemy import and_, or_

from . import app

PER_PAGE = 200


def paginate_query(query, offset, type):
    total_results = query.count()
    results = query.limit(PER_PAGE).offset(offset)
    result_count = results.count()
    return {
        "offset": offset,
        "resultsPerRequest": PER_PAGE,
        "totalResults": total_results,
        "resultsRemaining": total_results - offset - result_count,
        "userReleases": [serializer(item, type) for item in results],
    }


@app.route("/user/releases", methods=["GET"])
@auth.login_required
@require_apikey
def user_releases():
    try:
        offset = int(request.args.get("offset", 0))
    except ValueError:
        offset = 0

    artist_mbids = (
        db.session.query(UserArtist.mbid).filter(UserArtist.user_id == g.user.id).all()
    )
    query = (
        db.session.query(ArtistRelease, Release, UserRelease)
        .join(Release, Release.mbid == ArtistRelease.release_mbid)
        .filter(
            ArtistRelease.artist_mbid.in_(artist_mbids),
            Release.type.in_(g.user.filters),
        )
        .outerjoin(
            UserRelease,
            and_(UserRelease.mbid == Release.mbid, UserRelease.user_id == g.user.id),
        )
        .order_by(Release.date_release.desc())
    )
    data = paginate_query(query, offset, "user_release_quick")

    return response.success(data)


@app.route("/user/releases/global", methods=["GET"])
@auth.login_required
@require_apikey
def user_releases_global():
    try:
        offset = int(request.args.get("offset", 0))
    except ValueError:
        offset = 0

    query = (
        db.session.query(ArtistRelease, Release, UserRelease)
        .join(Release, Release.mbid == ArtistRelease.release_mbid)
        .filter(Release.type.in_(g.user.filters),)
        .outerjoin(
            UserRelease,
            and_(UserRelease.mbid == Release.mbid, UserRelease.user_id == g.user.id),
        )
        .order_by(Release.date_release.desc())
    )
    data = paginate_query(query, offset, "user_release_quick")

    return response.success(data)


@app.route("/user/artist/<string:mbid>/releases", methods=["GET"])
@auth.login_required
@require_apikey
def user_artist_releases(mbid):
    try:
        offset = int(request.args.get("offset", 0))
    except ValueError:
        offset = 0

    query = (
        db.session.query(ArtistRelease, Release, UserRelease)
        .join(Release, Release.mbid == ArtistRelease.release_mbid)
        .filter(ArtistRelease.artist_mbid == mbid, Release.type.in_(g.user.filters),)
        .outerjoin(
            UserRelease,
            and_(UserRelease.mbid == Release.mbid, UserRelease.user_id == g.user.id),
        )
        .order_by(Release.date_release.desc())
    )
    data = paginate_query(query, offset, "user_release_quick")
    return response.success(data)
