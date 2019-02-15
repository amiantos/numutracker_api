from datetime import datetime
from flask import request

import response
from .api_key import require_apikey
from backend.models import DeletedArtist, DeletedRelease
from backend.serializer import serializer
from numu import auth

from . import app


@app.route("/deletions", methods=["GET"])
@auth.login_required
@require_apikey
def deletions():
    try:
        date_offset = int(request.args.get("date_offset"))
    except (ValueError, TypeError):
        date_offset = None

    if date_offset is not None:
        try:
            date_offset = datetime.fromtimestamp(date_offset)
        except TypeError:
            date_offset = None

    if date_offset is None:
        return response.error("Argument date_offset is required for this endpoint.")

    release_deletions = DeletedRelease.query.filter(
        DeletedRelease.date_deleted >= date_offset
    ).all()
    artist_deletions = DeletedArtist.query.filter(
        DeletedArtist.date_deleted >= date_offset
    ).all()

    total_deletions = []
    total_deletions += release_deletions
    total_deletions += artist_deletions

    data = {
        "totalResults": len(total_deletions),
        "deletions": [serializer(deletion, "deletion") for deletion in total_deletions],
    }
    return response.success(data)
