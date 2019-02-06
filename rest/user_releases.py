from flask import g, jsonify, request
from datetime import date

import response
from backend.serializer import serializer
from backend.models import UserRelease
from numu import app as numu_app
from numu import auth

from . import app

PER_PAGE = 50


def paginate_query(query, page):
    paginated = query.paginate(page=page, per_page=PER_PAGE, error_out=True)
    return {
        "page": page,
        "perPage": PER_PAGE,
        "totalPages": paginated.pages,
        "nextPage": paginated.next_num,
        "prevPage": paginated.prev_num,
        "userReleases": [serializer(item, "user_release") for item in paginated.items],
    }


@app.route("/user/releases/unlistened", methods=["GET"])
@auth.login_required
def user_releases_unlistened_no_page():
    return user_releases_unlistened(1)


@app.route("/user/releases/unlistened/<int:page>", methods=["GET"])
@auth.login_required
def user_releases_unlistened(page):
    query = UserRelease.query.filter(
        UserRelease.user_id == g.user.id,
        UserRelease.type.in_(g.user.filters),
        UserRelease.listened.is_(False),
        UserRelease.date_release <= date.today(),
    ).order_by(UserRelease.date_release.desc())
    data = paginate_query(query, page)
    return response.success(data)


@app.route("/user/releases/all", methods=["GET"])
@auth.login_required
def user_releases_all_no_page():
    return user_releases_all(1)


@app.route("/user/releases/all/<int:page>", methods=["GET"])
@auth.login_required
def user_releases_all(page):
    query = UserRelease.query.filter(
        UserRelease.user_id == g.user.id,
        UserRelease.type.in_(g.user.filters),
        UserRelease.date_release <= date.today(),
    ).order_by(UserRelease.date_release.desc())
    data = paginate_query(query, page)
    return response.success(data)


@app.route("/user/releases/upcoming", methods=["GET"])
@auth.login_required
def user_releases_upcoming_no_page():
    return user_releases_upcoming(1)


@app.route("/user/releases/upcoming/<int:page>", methods=["GET"])
@auth.login_required
def user_releases_upcoming(page):
    query = UserRelease.query.filter(
        UserRelease.user_id == g.user.id,
        UserRelease.type.in_(g.user.filters),
        UserRelease.date_release > date.today(),
    ).order_by(UserRelease.date_release.asc())
    data = paginate_query(query, page)
    return response.success(data)


@app.route("/user/releases/new", methods=["GET"])
@auth.login_required
def user_releases_new_no_page():
    return user_releases_new(1)


@app.route("/user/releases/new/<int:page>", methods=["GET"])
@auth.login_required
def user_releases_new(page):
    # TODO: Needs to be redone to access notifications table?
    # Or at least ensure that date_added is working properly
    query = UserRelease.query.filter(
        UserRelease.user_id == g.user.id, UserRelease.type.in_(g.user.filters)
    ).order_by(UserRelease.date_added.desc())
    data = paginate_query(query, page)
    return response.success(data)
