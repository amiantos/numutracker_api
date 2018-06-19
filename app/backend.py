from sqlalchemy.sql import func

from main import app as numu_app
from main import db, celery

import musicbrainz as mb

from models import (
    Artist,
    ArtistAka,
    ArtistImport,
    Release,
    ReleaseType,
    AddMethod,
    UserRelease,
    UserArtist,
    ImportMethod
)


@celery.task
def import_artists(check_musicbrainz=True):
    import_artists = ArtistImport.query.filter_by(
        found_mbid=None
    ).order_by(
        ArtistImport.date_checked.desc(),
        ArtistImport.date_added.asc()
    ).limit(100).all()

    for i_artist in import_artists:
        found_artist = None
        print("Checking - {} {}".format(
            i_artist.import_name,
            i_artist.import_mbid))
        # Check local DB by mbid
        if i_artist.import_mbid and found_artist is None:
            print("Checking Stored MBID")
            found_artist = Artist.query.filter_by(
                mbid=i_artist.import_mbid).first()

        # Check local DB by name
        if found_artist is None:
            print("Checking by Name {}".format(i_artist.import_name))
            found_artist = Artist.query.filter_by(
                name=i_artist.import_name).first()

        # Check ArtistAKA table
        if found_artist is None:
            print("Checking Artist AKA")
            found_aka = ArtistAka.query.filter_by(
                name=i_artist.import_name).first()
            if found_aka:
                found_artist = Artist.query.filter_by(
                    mbid=found_aka.artist_mbid).first()

        if found_artist:
            print("Artist was found")
            i_artist.found_mbid = found_artist.mbid
            new_user_artist = UserArtist(
                user_id=i_artist.user_id,
                artist_mbid=found_artist.mbid,
                follow_method=i_artist.import_method
            )
            db.session.add(new_user_artist)

            continue

        # Grab from MusicBrainz
        if check_musicbrainz:
            mb_results = None
            if i_artist.import_mbid:
                mb_results = mb.get_artist(i_artist.import_mbid)

            if i_artist.import_mbid is None or mb_results is None or mb_results['artist'] is None:
                mb_results = mb.search_artist_by_name(i_artist.import_name)

            mb_artist = mb_results['artist']
            if mb_artist:
                found_artist = Artist(
                    mbid=mb_artist.get('id'),
                    name=mb_artist.get('name'),
                    sort_name=mb_artist.get('sort-name'),
                    disambiguation=mb_artist.get('disambiguation', '')
                )
                db.session.add(found_artist)
                db.session.commit()
                new_user_artist = UserArtist(
                    user_id=i_artist.user_id,
                    artist_mbid=mb_artist.get('id'),
                    follow_method=i_artist.import_method
                )
                db.session.add(new_user_artist)
                i_artist.found_mbid = mb_artist.get('id')
                print("Found in Music Brainz")
                db.session.commit()
                import_and_update_releases(found_artist.mbid, user_id=i_artist.user_id)

        i_artist.date_checked = func.now()
        db.session.add(i_artist)
        db.session.commit()

        import_and_update_releases


def import_and_update_releases(artist_mbid, user_id=None):
    mb_releases = mb.get_artist_releases(artist_mbid)

    releases_added = []

    for mb_release in mb_releases['releases']:
        numu_date = get_numu_date(mb_release.get('first-release-date'))
        if numu_date == '0000-01-01'\
                or mb_release.get('artist-credit') is None\
                or mb_release.get('id') in releases_added:
            continue

        release = Release.query.filter_by(mbid=mb_release.get('id')).first()
        if release is None:
            release = Release()

        release.mbid = mb_release.get('id')
        release.title = mb_release.get('title')
        release.type = get_numu_type(mb_release)
        release.date_release = get_numu_date(mb_release.get('first-release-date'))
        release.artists_string = mb_release.get('artist-credit-phrase')
        release.date_updated = func.now()

        for mb_artist in mb_release.get('artist-credit'):
            if type(mb_artist) == dict and mb_artist['artist']:
                artist = create_or_get_artist(mb_artist['artist']['id'])
                if artist and artist not in release.artists:
                    release.artists.append(artist)

        db.session.add(release)
        releases_added.append(release.mbid)

        if user_id:
            new_user_release = UserRelease(
                user_id=user_id,
                release_mbid=release.mbid,
                add_method=AddMethod.AUTOMATIC
            )
            db.session.add(new_user_release)

    db.session.commit()


def create_or_get_artist(artist_mbid):
    artist = Artist.query.filter_by(mbid=artist_mbid).first()
    if artist:
        return artist

    mb_artist = mb.get_artist(artist_mbid)

    if mb_artist['artist']:
        artist = Artist(
            mbid=mb_artist['artist'].get('id'),
            name=mb_artist['artist'].get('name'),
            sort_name=mb_artist['artist'].get('sort-name'),
            disambiguation=mb_artist['artist'].get('disambiguation', '')
        )
        db.session.add(artist)
        db.session.commit()
        return artist

    return None


def get_numu_date(mb_release_date):
    flat_date = mb_release_date.replace('-', '')
    year = flat_date[:4] or '0000'
    month = flat_date[4:6] or '01'
    day = flat_date[6:8] or '01'

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
