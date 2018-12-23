from flask import g, jsonify, request
from datetime import date

import response
from backend import repo, serializer
from backend.models import UserRelease
from numu import app as numu_app
from numu import auth
from sqlalchemy.orm import joinedload

from . import app


@app.route('/user/releases/unlistened/<int:page>', methods=['GET'])
@auth.login_required
def user_releases_unlistened(page):
    page = page if page else 1
    pages = UserRelease.query.filter(
        UserRelease.user_id == g.user.id,
        UserRelease.type.in_(('Album', 'EP')),
        UserRelease.listened.is_(False),
        UserRelease.date_release <= date.today().isoformat()
    ).options(
        joinedload('release')
    ).order_by(UserRelease.date_release.desc()).paginate(
        page=page,
        per_page=100,
        error_out=False
    )
    user_releases = pages.items
    return response.success(
        {
            'page': page,
            'per_page': 100,
            'total_pages': pages.pages,
            'next_page': pages.next_num,
            'prev_page': pages.prev_num,
            'items': serializer.user_releases(user_releases)})

@app.route('/user/releases/all', methods=['GET'])
@auth.login_required
def user_releases_all():
    pass

@app.route('/user/releases/upcoming', methods=['GET'])
@auth.login_required
def user_releases_upcoming():
    pass

@app.route('/user/releases/new', methods=['GET'])
@auth.login_required
def user_releases_new():
    pass
