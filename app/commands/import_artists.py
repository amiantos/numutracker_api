from utils import grab_json

from main import app
from main import db
from models import Artist


@app.cli.command()
def import_artists():
    """Import artist information from API V2."""
    print("Importing artists from V2")
    data = grab_json("https://numutracker.com/v2/json.php?all_artists&key={}"
                     .format(app.config.get('APIV2_KEY')))

    for artist in data:
        found_artist = Artist.query.filter_by(mbid=artist['mbid']).first()
        if found_artist is None:
            print("ADDED: {} - {}".format(artist['name'], artist['mbid']))
            new_artist = Artist(
                mbid=artist['mbid'],
                name=artist['name'],
                sort_name=artist['sort_name'],
                disambiguation=artist['disambiguation']
            )
            db.session.add(new_artist)

    db.session.commit()
