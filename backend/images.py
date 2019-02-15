from datetime import datetime, timedelta
from io import BytesIO
from urllib.parse import quote_plus

import boto3
import requests
from sqlalchemy import or_

from backend.models import Artist, Release, UserArtist, UserRelease
from backend.utils import grab_json
from numu import app as numu_app
from numu import db
from PIL import Image

session = boto3.session.Session()
client = session.client(
    "s3",
    region_name="sfo2",
    endpoint_url="https://sfo2.digitaloceanspaces.com",
    aws_access_key_id=numu_app.config.get("DO_ACCESS_KEY"),
    aws_secret_access_key=numu_app.config.get("DO_SECRET_KEY"),
)


def put_image_from_url(url, name):

    response = requests.get(url, stream=True)
    if response.status_code != 200:
        numu_app.logger.error(
            "Image at {} response code {}".format(url, response.status_code)
        )
        raise IOError("Unable to retrieve image file.")

    try:
        image = Image.open(response.raw)
    except TypeError as err:
        numu_app.logger.error(
            "Import of {} unsuccessful. Error message: {}".format(url, err)
        )
        raise IOError("Unable to process image file.")

    with BytesIO() as output:
        try:
            image.save(output, "png")
        except IOError as err:
            numu_app.logger.error(
                "Save of {} failed, Error message: {}".format(url, err)
            )
            raise err

        output.seek(0)
        client.upload_fileobj(
            output,
            "numu",
            name,
            ExtraArgs={"ACL": "public-read", "ContentType": "image/png"},
        )


def get_artist_art(artist):
    data = grab_json(
        "http://ws.audioscrobbler.com/2.0/?method=artist.getinfo"
        + "&artist={}&api_key={}&format=json".format(
            quote_plus(artist.name), numu_app.config.get("LAST_FM_API_KEY")
        )
    )

    images = data.get("artist", {}).get("image")
    if images:
        thumb_url = images[1]["#text"]
        full_url = images[2]["#text"]
        large_url = images[3]["#text"]

        if thumb_url and full_url and large_url:
            image_name = artist.mbid + ".png"
            try:
                put_image_from_url(thumb_url, "artist/thumb/" + image_name)
                put_image_from_url(full_url, "artist/full/" + image_name)
                put_image_from_url(large_url, "artist/large/" + image_name)
                return True
            except Exception as e:
                numu_app.logger.error("Put artist image failed: {}".format(e))
                return False
    numu_app.logger.info("No artist art found.")
    return False


def get_release_art(release):
    data = grab_json(
        "http://ws.audioscrobbler.com/2.0/?method=album.getinfo"
        + "&artist={}&album={}&api_key={}&format=json".format(
            quote_plus(release.artist_names),
            quote_plus(release.title),
            numu_app.config.get("LAST_FM_API_KEY"),
        )
    )

    images = data.get("album", {}).get("image")
    if images:
        thumb_url = images[1]["#text"]
        full_url = images[2]["#text"]
        large_url = images[3]["#text"]

        if thumb_url and full_url and large_url:
            image_name = release.mbid + ".png"
            try:
                put_image_from_url(thumb_url, "release/thumb/" + image_name)
                put_image_from_url(full_url, "release/full/" + image_name)
                put_image_from_url(large_url, "release/large/" + image_name)
                return True
            except Exception as e:
                numu_app.logger.error("Put release image failed: {}".format(e))
                return False
    numu_app.logger.info("No release art found.")
    return False


def scan_artist_art(limit=100):
    date_offset = datetime.now() - timedelta(days=14)
    artists = (
        Artist.query.filter(
            Artist.art.is_(False),
            or_(Artist.date_art_check < date_offset, Artist.date_art_check.is_(None)),
        )
        .order_by(Artist.date_art_check.asc().nullsfirst())
        .limit(limit)
        .all()
    )

    for artist in artists:
        numu_app.logger.info(
            "Checking art for artist {}, last check: {}".format(
                artist.name, artist.date_art_check
            )
        )
        art_success = get_artist_art(artist)
        if art_success:
            artist.art = True

        artist.date_art_check = datetime.now()
        db.session.add(artist)
    db.session.commit()

    return True


def scan_release_art(limit=100):
    date_offset = datetime.now() - timedelta(days=14)
    releases = (
        Release.query.filter(
            Release.art.is_(False),
            or_(Release.date_art_check < date_offset, Release.date_art_check.is_(None)),
        )
        .order_by(Release.date_art_check.asc().nullsfirst())
        .limit(limit)
        .all()
    )

    for release in releases:
        numu_app.logger.info(
            "Checking art for release {} - {}, last check: {}".format(
                release.artist_names, release.title, release.date_art_check
            )
        )
        art_success = get_release_art(release)
        if art_success:
            release.art = True
        release.date_art_check = datetime.now()
        db.session.add(release)
    db.session.commit()

    return True
