from datetime import date

from flask import g, request

import response
from backend.models import UserRelease, Release, ArtistRelease, UserArtist
from backend.serializer import serializer
from numu import auth, db
from sqlalchemy import and_, or_

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
        "userReleases": [serializer(item, type) for item in results],
    }


@app.route("/user/releases", methods=["GET"])
@auth.login_required
def user_releases():
    try:
        offset = int(request.args.get("offset", 0))
    except ValueError:
        offset = 0
    artist_mbids = (
        db.session.query(UserArtist.mbid)
        .filter(UserArtist.user_id == g.user.id, UserArtist.following.is_(True))
        .all()
    )
    query = (
        db.session.query(ArtistRelease, Release, UserRelease)
        .join(Release)
        .outerjoin(
            UserRelease,
            and_(UserRelease.mbid == Release.mbid, UserRelease.user_id == g.user.id),
        )
        .filter(
            or_(
                ArtistRelease.artist_mbid.in_(artist_mbids),
                UserRelease.following.is_(True),
            ),
            Release.type.in_(g.user.filters),
        )
        .order_by(UserRelease.date_updated.desc(), Release.date_updated.desc())
    )
    data = paginate_query(query, offset, "user_release")
    return response.success(data)


@app.route("/user/artist/<string:mbid>/releases", methods=["GET"])
@auth.login_required
def user_artist_releases(mbid):
    try:
        offset = int(request.args.get("offset", 0))
    except ValueError:
        offset = 0
    query = (
        db.session.query(ArtistRelease, Release, UserRelease)
        .join(Release)
        .filter(ArtistRelease.artist_mbid == mbid, Release.type.in_(g.user.filters))
        .outerjoin(
            UserRelease,
            and_(UserRelease.mbid == Release.mbid, UserRelease.user_id == g.user.id),
        )
        .order_by(Release.date_release.desc())
    )
    data = paginate_query(query, offset, "user_release")
    return response.success(data)
