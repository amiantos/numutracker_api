from flask import Blueprint

app = Blueprint("commands", __name__)

from . import (
    import_artists,
    check_art,
    mb_processing,
    user_processing,
    import_user_data,
)

