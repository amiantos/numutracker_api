"""Import artist data from other services or apps."""
from datetime import datetime, timedelta

from sqlalchemy import or_
from sqlalchemy.sql import func

from backend import data_processing, repo
from backend.models import ArtistImport
from backend.utils import grab_json
from numu import app as numu_app
from numu import db


def import_artists_v2(user, artists):
    artists_added = 0
    for artist in artists:
        found_import = ArtistImport.query.filter(
            ArtistImport.user_id == user.id,
            or_(
                ArtistImport.import_name == artist["name"],
                ArtistImport.import_mbid == artist["mbid"],
            ),
        ).first()
        if found_import is None:
            new_import = ArtistImport(
                user_id=user.id,
                import_name=artist["name"],
                import_mbid=artist["mbid"],
                import_method="V2",
            )
            db.session.add(new_import)
            artists_added += 1

    if artists_added > 0:
        db.session.commit()

    return artists_added

