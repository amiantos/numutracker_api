from datetime import datetime, timedelta

import musicbrainz as mb
from main import app as numu_app
from main import celery, db
from models import (AddMethod, Artist, ArtistAka, ArtistImport, ImportMethod,
                    Release, ReleaseType, UserArtist, UserNotifications,
                    UserRelease)
from sqlalchemy import or_
from sqlalchemy.sql import func

date_filter = datetime.now() - timedelta(days=3)


# ------------------------------------------------------------------------
# Fetch Data
# ------------------------------------------------------------------------


def get_numu_artist_by_mbid(mbid):
    return Artist.query.filter_by(mbid=mbid).first()


def get_numu_artist_by_name(name):
    artist = Artist.query.filter(
        Artist.name.ilike("%{}%".format(name))).first()
    if artist is None:
        aka = ArtistAka.query.filter(
            ArtistAka.name.ilike("%{}%".format(name))).first()
        if aka:
            artist = Artist.query.filter_by(mbid=aka.artist_mbid).first()
    return artist


def get_numu_release(release_mbid):
    return Release.query.filter_by(mbid=release_mbid).first()


def add_numu_artist_from_mb(artist_name=None, artist_mbid=None):
    mb_results = mb.get_artist(artist_mbid)

    if artist_name and mb_results and mb_results.get('status') != 200:
        mb_results = mb.search_artist_by_name(artist_name)

    if mb_results and mb_results.get('status') == 200:
        mb_artist = mb_results['artist']
        artist = get_numu_artist_by_mbid(mb_artist['id'])
        if artist is None:
            artist = Artist(
                mbid=mb_artist.get('id'),
                name=mb_artist.get('name'),
                sort_name=mb_artist.get('sort-name'),
                disambiguation=mb_artist.get('disambiguation', ''),
                date_updated=func.now()
            )
            db.session.add(artist)
            db.session.commit()

        return artist

    return None


def add_numu_releases_from_mb(artist):
    """Add new releases from musicbrainz."""
    mb_releases = mb.get_artist_releases(artist.mbid)
    releases_added = []

    if mb_releases['status'] != 200:
        return None

    for mb_release in mb_releases['releases']:
        if mb_release.get('id') in releases_added:
            continue

        release = get_numu_release(mb_release.get('id'))

        if release is None:
            release = create_or_update_numu_release(mb_release)

        if release:
            releases_added.append(release.mbid)

    artist.date_checked = func.now()
    db.session.add(artist)
    db.session.commit()

    return releases_added


def create_or_update_numu_release(mb_release):
    """Parse an MB release and turn it into a release object.

    Returns (unsaved) release object."""
    numu_date = get_numu_date(mb_release.get('first-release-date'))
    if numu_date is None or mb_release.get('artist-credit') is None:
        return None

    release = get_numu_release(mb_release.get('id'))
    if release is None:
        release = Release()

    release.mbid = mb_release.get('id')
    release.title = mb_release.get('title')
    release.type = get_numu_type(mb_release)
    release.date_release = numu_date
    release.artists_string = mb_release.get('artist-credit-phrase')
    release.date_updated = func.now()

    db.session.add(release)
    db.session.commit()

    for mb_artist in mb_release.get('artist-credit'):
        if type(mb_artist) == dict and mb_artist['artist']:
            artist = get_numu_artist_by_mbid(mb_artist['artist']['id'])
            if artist is None:
                artist = add_numu_artist_from_mb(
                    artist_mbid=mb_artist['artist']['id'])
            if artist and artist not in release.artists:
                release.artists.append(artist)

    db.session.add(release)
    db.session.commit()

    return release


# ------------------------------------------------------------------------
# Update Data
# ------------------------------------------------------------------------


def update_numu_artist_from_mb(artist):
    mb_result = mb.get_artist(artist.mbid)
    status = mb_result['status']
    mb_artist = mb_result['artist']
    changed = False

    if status == 404:
        # Artist has been deleted
        artist.active = False
        changed = True

    if status == 200 and mb_artist['id'] != artist.mbid:
        # Artist has been merged
        # TODO: Get followers for artist and follow the new artist
        artist.active = False
        changed = True

    if status == 200:
        if artist.name != mb_artist['name']:
            artist.name = mb_artist['name']
            changed = True
        if artist.sort_name != mb_artist['sort-name']:
            artist.sort_name = mb_artist['sort-name']
            changed = True
        if artist.disambiguation != mb_artist.get('disambiguation', ''):
            artist.disambiguation = mb_artist.get('disambiguation', '')
            changed = True

    if changed or artist.date_updated is None:
        artist.date_updated = func.now()
        # TODO: Update all instances of user artist

    # Add any new releases from MusicBrainz
    add_numu_releases_from_mb(artist)

    # Update user releases
    notifications = False if artist.date_checked is None else True
    update_numu_user_releases(artist.mbid, notifications)

    artist.date_checked = func.now()
    db.session.add(artist)
    db.session.commit()

    return artist

"""
def update_numu_release_from_mb(release):
    mb_result = mb.get_numu_release(release.mbid)
    status = mb_result['status']
    mb_release = mb_result['release']

    if status == 404:
        # Release has been deleted
        release.active = False

    if status == 200 and mb_release['id'] != release.mbid:
        # Release MBID is different, release has been merged
        # TODO: Check for different release in DB
        # TODO: Update any user information to the different release
        release.active = False

    if status == 200:
        release = create_or_update_numu_release(mb_release)

    db.session.add(release)
    db.session.commit()
    return release
"""


# ------------------------------------------------------------------------
# Create Relationships
# ------------------------------------------------------------------------


def create_user_numu_artist(user_id, artist, import_method):
    user_artist = UserArtist.query.filter_by(
        user_id=user_id,
        mbid=artist.mbid
    ).first()
    if user_artist is None:
        user_artist = UserArtist(
            user_id=user_id,
            mbid=artist.mbid,
            name=artist.name,
            sort_name=artist.sort_name,
            disambiguation=artist.disambiguation,
            art=artist.art,
            apple_music_link=artist.apple_music_link,
            spotify_link=artist.spotify_link,
            follow_method=import_method,
            date_followed=func.now(),
            following=True
        )
    db.session.add(user_artist)
    db.session.commit()

    update_numu_user_releases(artist.mbid, notifications=False)

    return user_artist


def update_numu_user_releases(artist_mbid, notifications=True):
    """Create or update user releases for an artist."""
    user_artists = UserArtist.query.filter_by(mbid=artist_mbid).all()
    releases = Artist.query.filter_by(mbid=artist_mbid).first().releases

    for user_artist in user_artists:
        for release in releases:
            notify = False

            user_release = UserRelease.query.filter_by(
                user_id=user_artist.user_id, mbid=release.mbid).first()
            if user_release is None:
                user_release = UserRelease()
                user_release.add_method = AddMethod.AUTOMATIC
                notify = True
            user_release.user_id = user_artist.user_id
            user_release.mbid = release.mbid
            user_release.title = release.title
            user_release.artists_string = release.artists_string
            user_release.type = release.type
            user_release.date_release = release.date_release
            user_release.art = release.art
            user_release.apple_music_link = release.apple_music_link
            user_release.spotify_link = release.spotify_link
            user_release.date_updated = func.now()
            db.session.add(user_release)
            db.session.commit()

            # TODO: Process Notifications
            if notify and notifications:
                numu_app.logger.info("Generating notifications...")
                pass
            else:
                numu_app.logger.info("No notifications...")


# ------------------------------------------------------------------------
# Tasks
# ------------------------------------------------------------------------


@celery.task
def update_artists():
    limit = 100

    artists_to_update = Artist.query.filter(
        or_(Artist.date_checked <= date_filter,
            Artist.date_checked.is_(None))
    ).order_by(
        Artist.date_added.asc(),
        Artist.date_checked.asc()
    ).limit(limit).all()

    for artist in artists_to_update:
        update_numu_artist_from_mb(artist)


@celery.task
def process_imported_artists(check_musicbrainz=True):
    limit = 1000
    if check_musicbrainz:
        limit = 100

    artist_imports = ArtistImport.query.filter(
        ArtistImport.found_mbid.is_(None),
        or_(ArtistImport.date_checked <= date_filter,
            ArtistImport.date_checked.is_(None))
    ).order_by(
        ArtistImport.date_checked.asc(),
        ArtistImport.date_added.asc()
    ).limit(limit).all()

    for artist_import in artist_imports:
        numu_app.logger.info("Checking {} {}".format(
            artist_import.user_id,
            artist_import.import_name))

        numu_app.logger.info("Searching locally by name...")
        found_artist = get_numu_artist_by_name(artist_import.import_name)

        if found_artist is None and check_musicbrainz:
            numu_app.logger.info("Searching MusicBrainz...")
            found_artist = add_numu_artist_from_mb(
                artist_name=artist_import.import_name,
                artist_mbid=artist_import.import_mbid
            )
            # Add releases
            if found_artist:
                add_numu_releases_from_mb(found_artist.mbid)

        if found_artist is not None:
            numu_app.logger.info("Found artist!")
            artist_import.found_mbid = found_artist.mbid
            create_user_numu_artist(
                artist_import.user_id,
                found_artist,
                artist_import.import_method)

        else:
            numu_app.logger.info("Did not find artist.")
            if check_musicbrainz:
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
