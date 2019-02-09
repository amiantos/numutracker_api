from datetime import date

from flask import g

import response
from backend.models import UserRelease
from backend.serializer import serializer
from numu import auth

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


@app.route("/user/releases/unlistened", methods=["GET"])
@auth.login_required
def user_releases_unlistened_no_page():
    return user_releases_unlistened(0)


@app.route("/user/releases/unlistened/<int:offset>", methods=["GET"])
@auth.login_required
def user_releases_unlistened(offset):
    query = UserRelease.query.filter(
        UserRelease.user_id == g.user.id,
        UserRelease.type.in_(g.user.filters),
        UserRelease.listened.is_(False),
        UserRelease.following.is_(True),
        UserRelease.date_release <= date.today(),
    ).order_by(UserRelease.date_release.desc())
    data = paginate_query(query, offset, "user_release")
    return response.success(data)


@app.route("/user/releases/all", methods=["GET"])
@auth.login_required
def user_releases_all_no_page():
    return user_releases_all(0)


@app.route("/user/releases/all/<int:offset>", methods=["GET"])
@auth.login_required
def user_releases_all(offset):
    query = UserRelease.query.filter(
        UserRelease.user_id == g.user.id,
        UserRelease.type.in_(g.user.filters),
        UserRelease.following.is_(True),
        UserRelease.date_release <= date.today(),
    ).order_by(UserRelease.date_release.desc())
    data = paginate_query(query, offset, "user_release")
    return response.success(data)


@app.route("/user/releases/upcoming", methods=["GET"])
@auth.login_required
def user_releases_upcoming_no_offset():
    return user_releases_upcoming(0)


@app.route("/user/releases/upcoming/<int:offset>", methods=["GET"])
@auth.login_required
def user_releases_upcoming(offset):
    query = UserRelease.query.filter(
        UserRelease.user_id == g.user.id,
        UserRelease.type.in_(g.user.filters),
        UserRelease.following.is_(True),
        UserRelease.date_release > date.today(),
    ).order_by(UserRelease.date_release.asc())
    data = paginate_query(query, offset, "user_release")
    return response.success(data)


@app.route("/user/releases/new", methods=["GET"])
@auth.login_required
def user_releases_new_no_offset():
    return user_releases_new(0)


@app.route("/user/releases/new/<int:offset>", methods=["GET"])
@auth.login_required
def user_releases_new(offset):
    # TODO: Needs to be redone to access notifications table?
    # Or at least ensure that date_added is working properly
    query = UserRelease.query.filter(
        UserRelease.user_id == g.user.id,
        UserRelease.type.in_(g.user.filters),
        UserRelease.following.is_(True),
    ).order_by(UserRelease.date_added.desc())
    data = paginate_query(query, offset, "user_release")
    return response.success(data)
