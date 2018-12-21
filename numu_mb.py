"""The bridge between Numu and Musicbrainz."""

import musicbrainz as mb
from models import Artist, Release, UserArtist, UserRelease
import repo
from sqlalchemy.sql import func
from numu import db, app as numu_app


# ------------------------------------------------------------------------
# Add / Update Core Data
# ------------------------------------------------------------------------


def add_numu_artist_from_mb(artist_name=None, artist_mbid=None):
    mb_results = mb.get_artist(artist_mbid)

    if artist_name and mb_results and mb_results.get('status') != 200:
        mb_results = mb.search_artist_by_name(artist_name)

    if mb_results and mb_results.get('status') == 200:
        mb_artist = mb_results['artist']
        artist = repo.get_numu_artist_by_mbid(mb_artist['id'])
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
        numu_app.logger.info("No releases found.")
        return None

    for mb_release in mb_releases['releases']:
        if mb_release.get('id') in releases_added:
            continue

        release = repo.get_numu_release(mb_release.get('id'))

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
    Returns release object."""
    numu_date = get_numu_date(mb_release.get('first-release-date'))
    if numu_date is None or mb_release.get('artist-credit') is None:
        return None

    release = repo.get_numu_release(mb_release.get('id'))
    if release is None:
        release = Release()

    release.mbid = mb_release.get('id')
    release.title = mb_release.get('title')
    release.type = get_numu_type(mb_release)
    release.date_release = numu_date
    artist_names = mb_release.get('artist-credit-phrase')
    if len(artist_names) > 40:
        artist_names = "Various Artists"
    release.artist_names = artist_names
    release.date_updated = func.now()

    db.session.add(release)
    db.session.commit()

    for mb_artist in mb_release.get('artist-credit'):
        if type(mb_artist) == dict and mb_artist['artist']:
            artist = repo.get_numu_artist_by_mbid(mb_artist['artist']['id'])
            if artist is None:
                artist = add_numu_artist_from_mb(artist_mbid=mb_artist['artist']['id'])
            if artist and artist not in release.artists:
                release.artists.append(artist)

    db.session.add(release)
    db.session.commit()

    return release


# ------------------------------------------------------------------------
# Update Data
# ------------------------------------------------------------------------

def delete_numu_artist(artist):
    """Delete provided Numu Artist"""
    # Delete all releases
    for release in artist.releases:
        db.session.delete(release)
    # Delete artist
    db.session.delete(artist)
    db.session.commit()
    return True


def update_numu_artist_from_mb(artist):
    mb_result = mb.get_artist(artist.mbid)
    status = mb_result['status']
    mb_artist = mb_result['artist']
    changed = False

    if status == 404:
        # Artist has been deleted
        numu_app.logger.info("Artist Deleted: {}".format(artist))
        delete_numu_artist(artist)
        return None

    if status == 200 and mb_artist['id'] != artist.mbid:
        # Artist has been merged
        new_mbid = mb_artist['id']
        numu_app.logger.info("Artist Merged: {}, New MBID: {}".format(artist, new_mbid))
        new_artist = repo.get_numu_artist_by_mbid(new_mbid)
        if not new_artist:
            new_artist = add_numu_artist_from_mb(artist_mbid=new_mbid)
            add_numu_releases_from_mb(new_artist)
        user_artists = UserArtist.query.filter_by(mbid=new_mbid).all()
        for user_artist in user_artists:
            user_artist.mbid = new_artist.mbid
            user_artist.date_updated = None
            db.session.add(user_artist)
        db.session.commit()
        delete_numu_artist(artist)
        changed = True
        artist = new_artist
    
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
        numu_app.logger.info("Changes Detected! Updating User Artists...")
        artist.date_updated = func.now()
        user_artists = UserArtist.query.filter_by(mbid=artist.mbid).all()
        for user_artist in user_artists:
            update_user_artist(user_artist, artist)

    # Add any new releases from MusicBrainz
    add_numu_releases_from_mb(artist)

    # Update user releases
    notifications = False if artist.date_checked is None else True
    update_all_user_releases(artist.mbid, notifications)

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

def update_user_artist(user_artist, new_artist):
    user_artist.name = new_artist.name
    user_artist.sort_name = new_artist.sort_name
    user_artist.disambiguation = new_artist.disambiguation
    user_artist.art = new_artist.art
    user_artist.date_updated = new_artist.date_updated
    user_artist.apple_music_link = new_artist.apple_music_link
    user_artist.spotify_link = new_artist.spotify_link

    db.session.add(user_artist)
    db.session.commit()
    return user_artist


def create_or_update_user_artist(user_id, artist, import_method):
    user_artist = UserArtist.query.filter_by(
        user_id=user_id,
        mbid=artist.mbid
    ).first()
    if user_artist is None:
        user_artist = UserArtist(
            user_id=user_id,
            mbid=artist.mbid,
            follow_method=import_method,
            date_followed=func.now(),
            following=True
        )
    user_artist.name = artist.name
    user_artist.sort_name = artist.sort_name
    user_artist.disambiguation = artist.disambiguation
    user_artist.art = artist.art
    user_artist.date_updated = artist.date_updated
    user_artist.apple_music_link = artist.apple_music_link
    user_artist.spotify_link = artist.spotify_link

    db.session.add(user_artist)
    db.session.commit()

    return user_artist


def create_or_update_user_releases(user_artist, notifications=True):
    """Create or update user releases for an artist."""
    releases = repo.get_numu_artist_releases(user_artist.mbid)

    for release in releases:
        notify = False

        user_release = UserRelease.query.filter_by(
            user_id=user_artist.user_id, mbid=release.mbid).first()
        if user_release is None:
            user_release = UserRelease()
            user_release.add_method = 'automatic'
            user_release.user_id = user_artist.user_id
            user_release.mbid = release.mbid
            notify = True
        user_release.title = release.title
        user_release.artist_names = release.artist_names
        user_release.type = release.type
        user_release.date_release = release.date_release
        user_release.art = release.art
        user_release.apple_music_link = release.apple_music_link
        user_release.spotify_link = release.spotify_link
        user_release.date_updated = release.date_updated
        db.session.add(user_release)
        db.session.commit()

        # TODO: Process Notifications
        if notify and notifications:
            """Create Notification"""
            pass


def update_all_user_releases(artist_mbid, notifications=True):
    user_artists = UserArtist.query.filter_by(mbid=artist_mbid).all()

    for user_artist in user_artists:
        create_or_update_user_releases(user_artist, notifications)


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
        return 'Live'
    if 'Compilation' in secondary_types or primary_type == 'Compilation':
        return 'Compilation'
    if 'Remix' in secondary_types or primary_type == 'Remix':
        return 'Remix'
    if 'Soundtrack' in secondary_types or primary_type == 'Soundtrack':
        return 'Soundtrack'
    if 'Interview' in secondary_types or primary_type == 'Interview':
        return 'Interview'
    if 'Spokenword' in secondary_types or primary_type == 'Spokenword':
        return 'Spokenword'
    if 'Audiobook' in secondary_types or primary_type == 'Audiobook':
        return 'Audiobook'
    if 'Mixtape' in secondary_types or primary_type == 'Mixtape':
        return 'Mixtape'
    if 'Demo' in secondary_types or primary_type == 'Demo':
        return 'Demo'
    if 'DJ-mix' in secondary_types or primary_type == 'DJ-mix':
        return 'DJ-mix'
    if primary_type == 'Album':
        return 'Album'
    if primary_type == 'EP':
        return 'EP'
    if primary_type == 'Single':
        return 'Single'
    if primary_type == 'Broadcast':
        return 'Broadcast'
    if primary_type == 'Other':
        return 'Other'
    return 'Unknown'
