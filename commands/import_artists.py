from backend.models import Artist, ArtistAka
from numu import app as numu_app, db
from backend.utils import grab_json


@numu_app.cli.command()
def import_artists():
    """Import artist information from API V2."""
    limit = 200
    offset = 0
    total = 0
    processing = True

    print("Importing artists from V2")

    while processing is True:
        uri = "https://numutracker.com/v2/json.php?all_artists"
        + "&key={}&limit={}&offset={}".format(
            numu_app.config.get('NUMU_V2_API_KEY'), limit, offset)
        data = grab_json(uri)
        if not data:
            processing = False

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

        offset += limit
        total += limit

        print("Processed {} Next offset: {}".format(total, offset))

    print("Importing artist AKA from V2")

    data = grab_json(
        "https://numutracker.com/v2/json.php?all_artist_aka&key={}".format(
            numu_app.config.get('NUMU_V2_API_KEY')))

    for aka in data:
        found_artist = Artist.query.filter_by(mbid=aka['mbid']).first()
        if found_artist is not None:
            found_aka = ArtistAka.query.filter_by(
                artist_mbid=aka['mbid'], name=aka['aka_name']).first()
            if found_aka is None:
                print("ADDED AKA: {} - AKA: {}".format(
                    found_artist.name, aka['aka_name']))
                new_aka = ArtistAka(
                    artist_mbid=found_artist.mbid,
                    name=aka['aka_name']
                )
                db.session.add(new_aka)

    db.session.commit()
