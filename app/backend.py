from sqlalchemy.sql import func
from datetime import datetime, timedelta
import musicbrainz as mb
from main import app as numu_app
from main import celery, db
from models import (AddMethod, Artist, ArtistAka, ArtistImport, ImportMethod,
                    Release, ReleaseType, UserArtist, UserRelease)


date_filter = datetime.now() - timedelta(days=3)


# ------------------------------------------------------------------------
# Fetch Data
# ------------------------------------------------------------------------


def get_artist_by_mbid(mbid):
    return Artist.query.filter_by(mbid=mbid).first()


def get_artist_by_name(name):
    artist = Artist.query.filter_by(name=name).first()
    if artist is None:
        aka = ArtistAka.query.filter_by(name=name).first()
        if aka:
            artist = Artist.query.filter_by(mbid=aka.artist_mbid).first()
    return artist


def get_release(release_mbid):
    return Release.query.filter_by(mbid=release_mbid).first()


def add_artist_from_mb(artist_name=None, artist_mbid=None):
    mb_results = mb.get_artist(artist_mbid)

    if mb_results['status'] != 200 and artist_name:
        mb_results = mb.search_artist_by_name(artist_name)

    if mb_results['status'] == 200:
        mb_artist = mb_results['artist']
        new_artist = get_artist_by_mbid(mb_artist['id'])
        if new_artist is None:
            new_artist = Artist(
                mbid=mb_artist.get('id'),
                name=mb_artist.get('name'),
                sort_name=mb_artist.get('sort-name'),
                disambiguation=mb_artist.get('disambiguation', '')
            )
            db.session.add(new_artist)
            db.session.commit()
        return new_artist

    return None


def add_releases_from_mb(artist_mbid):
    mb_releases = mb.get_artist_releases(artist_mbid)
    releases_added = []

    if mb_releases['status'] != 200:
        return None

    for mb_release in mb_releases['releases']:
        if mb_release.get('id') in releases_added:
            continue

        release = get_release(mb_release.get('id'))
        if release is None:
            release = parse_mb_release(mb_release)
            if release:
                db.session.add(release)
        if release:
            releases_added.append(release.mbid)

    db.session.commit()
    return releases_added


def parse_mb_release(mb_release):
    numu_date = get_numu_date(mb_release.get('first-release-date'))
    if numu_date is None or mb_release.get('artist-credit') is None:
        return None

    release = get_release(mb_release.get('id'))
    if release is None:
        release = Release()

    release.mbid = mb_release.get('id')
    release.title = mb_release.get('title')
    release.type = get_numu_type(mb_release)
    release.date_release = numu_date
    release.artists_string = mb_release.get('artist-credit-phrase')
    release.date_updated = func.now()

    # Clear release artists before re-creating
    release.artists = []

    for mb_artist in mb_release.get('artist-credit'):
        if type(mb_artist) == dict and mb_artist['artist']:
            artist = get_artist_by_mbid(mb_artist['artist']['id'])
            if artist is None:
                artist = add_artist_from_mb(
                    artist_mbid=mb_artist['artist']['id'])
            if artist and artist not in release.artists:
                release.artists.append(artist)

    return release


# ------------------------------------------------------------------------
# Update Data
# ------------------------------------------------------------------------


def update_artist_from_mb(artist):
    mb_result = mb.get_artist(artist.mbid)
    status = mb_result['status']
    mb_artist = mb_result['artist']

    if status == 404:
        # Artist has been deleted
        artist.active = False

    if status == 200 and mb_artist['id'] != artist.mbid:
        # Artist has been merged
        # TODO: Get followers for artist and ensure they've followed the new artist
        artist.active = False

    if status == 200:
        artist.name = mb_artist['name']
        artist.sort_name = mb_artist['sort-name']
        artist.disambiguation = mb_artist.get('disambiguation', '')

    # Update releases
    for release in artist.releases:
        update_release_from_mb(release)

    # Add releases
    add_releases_from_mb(artist.mbid)

    # Update user releases
    user_artists = UserArtist.query.filter_by(artist_mbid=artist.mbid).all()
    for user_artist in user_artists:
        create_user_releases(user_artist)

    artist.date_updated = func.now()
    db.session.add(artist)
    db.session.commit()

    return artist


def update_release_from_mb(release):
    mb_result = mb.get_release(release.mbid)
    status = mb_result['status']
    mb_release = mb_result['release']

    if status == 404:
        # Release has been deleted
        release.active = False

    if status == 200 and mb_release['id'] != release.mbid:
        # Release MBID is different, release has been merged
        # Mark release as deleted
        # Check for different release in DB
        # Update any user information to the different release
        release.active = False

    if status == 200:
        release = parse_mb_release(mb_release)

    db.session.add(release)
    db.session.commit()
    return release


# ------------------------------------------------------------------------
# Create Relationships
# ------------------------------------------------------------------------


def create_user_artist(user_id, artist_mbid, import_method):
    user_artist = UserArtist.query.filter_by(
        user_id=user_id,
        artist_mbid=artist_mbid
    ).first()
    if user_artist is None:
        user_artist = UserArtist(
            user_id=user_id,
            artist_mbid=artist_mbid,
            follow_method=import_method
        )
    db.session.add(user_artist)
    db.session.commit()
    return user_artist


def create_user_releases(user_artist):
    user = user_artist.user
    artist = user_artist.artist

    for release in artist.releases:
        user_release = UserRelease.query.filter_by(
            user_id=user.id,
            release_mbid=release.mbid).first()
        if user_release is None:
            user_release = UserRelease(
                user_id=user.id,
                release_mbid=release.mbid,
                add_method=AddMethod.AUTOMATIC
            )
        db.session.add(user_release)

    db.session.commit()


# ------------------------------------------------------------------------
# Tasks
# ------------------------------------------------------------------------

@celery.task
def update_artists():
    limit = 100

    artists_to_update = Artist.query.filter(
        Artist.date_updated <= date_filter
    ).order_by(
        Artist.date_updated.asc()
    ).limit(limit).all()

    for artist in artists_to_update:
        update_artist_from_mb(artist)


@celery.task
def process_imported_artists(check_musicbrainz=True):
    limit = 1000
    if check_musicbrainz:
        limit = 100

    artist_imports = ArtistImport.query.filter(
        ArtistImport.found_mbid is None,
        ArtistImport.date_checked <= date_filter
    ).order_by(
        ArtistImport.date_checked.asc(),
        ArtistImport.date_added.asc()
    ).limit(limit).all()

    for artist_import in artist_imports:
        found_artist = None

        numu_app.logger.info("Checking {} {} {}".format(
            artist_import.user_id,
            artist_import.import_name,
            artist_import.import_mbid))

        if artist_import.import_mbid:
            numu_app.logger.info("Searching locally by MBID...")
            found_artist = get_artist_by_mbid(artist_import.import_mbid)

        if found_artist is None:
            numu_app.logger.info("Searching locally by name...")
            found_artist = get_artist_by_name(artist_import.import_name)

        if found_artist:
            numu_app.logger.info("Artist found locally.")

            artist_import.found_mbid = found_artist.mbid
            db.session.add(artist_import)

            user_artist = create_user_artist(
                artist_import.user_id,
                found_artist.mbid,
                artist_import.import_method)

            create_user_releases(user_artist)

            continue

        if check_musicbrainz:
            numu_app.logger.info("Not Found Locally, Creating...")
            found_artist = add_artist_from_mb(
                artist_name=artist_import.import_name,
                artist_mbid=artist_import.import_mbid
            )
            artist_import.found_mbid = found_artist.mbid
            add_releases_from_mb(found_artist.mbid)
            user_artist = create_user_artist(
                artist_import.user_id,
                found_artist.mbid,
                artist_import.import_method)
            create_user_releases(user_artist)

        artist_import.date_checked = func.now()
        db.session.add(artist_import)

    db.session.commit()


# ------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------


def get_numu_date(mb_release_date):
    flat_date = mb_release_date.replace('-', '')
    year = flat_date[:4] or '0000'
    month = flat_date[4:6] or '01'
    day = flat_date[6:8] or '01'

    if year == '0000' or year == '????':
        return None

    return "{}-{}-{}".format(year, month, day)


def get_numu_type(mb_release):
    primary_type = mb_release.get('primary-type')
    secondary_types = mb_release.get('secondary-type-list', {})
    if 'Live' in secondary_types or primary_type == 'Live':
        return ReleaseType.LIVE
    if 'Compilation' in secondary_types or primary_type == 'Compilation':
        return ReleaseType.COMPILATION
    if 'Remix' in secondary_types or primary_type == 'Remix':
        return ReleaseType.REMIX
    if 'Soundtrack' in secondary_types or primary_type == 'Soundtrack':
        return ReleaseType.SOUNDTRACK
    if 'Interview' in secondary_types or primary_type == 'Interview':
        return ReleaseType.INTERVIEW
    if 'Spokenword' in secondary_types or primary_type == 'Spokenword':
        return ReleaseType.SPOKENWORD
    if 'Audiobook' in secondary_types or primary_type == 'Audiobook':
        return ReleaseType.AUDIOBOOK
    if 'Mixtape' in secondary_types or primary_type == 'Mixtape':
        return ReleaseType.MIX_TAPE
    if 'Demo' in secondary_types or primary_type == 'Demo':
        return ReleaseType.DEMO
    if 'DJ-mix' in secondary_types or primary_type == 'DJ-mix':
        return ReleaseType.DJ_MIX
    if primary_type == 'Album':
        return ReleaseType.ALBUM
    if primary_type == 'EP':
        return ReleaseType.EP
    if primary_type == 'Single':
        return ReleaseType.SINGLE
    if primary_type == 'Broadcast':
        return ReleaseType.BROADCAST
    if primary_type == 'Other':
        return ReleaseType.OTHER
    return ReleaseType.UNKNOWN
