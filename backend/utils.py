import json
from datetime import datetime
from uuid import uuid4

import pytz
import requests


def grab_json(uri):
    try:
        response = requests.get(uri)
    except requests.ConnectionError:
        return None
    return json.loads(response.text)


def now():
    return datetime.now(pytz.utc)


def uuid():
    return str(uuid4())


def convert_mb_release_date(mb_release_date):
    if mb_release_date is None:
        return None

    flat_date = mb_release_date.replace("-", "")
    year = flat_date[:4] or "0000"
    month = flat_date[4:6] or "01"
    day = flat_date[6:8] or "01"

    if month == "??" or day == "00":
        month = "01"
    if day == "??" or day == "00":
        day = "01"
    if year == "0000" or year == "????":
        return None

    return "{}-{}-{}".format(year, month, day)


def get_release_type(mb_release):
    primary_type = mb_release.get("primary-type")
    secondary_types = mb_release.get("secondary-type-list", {})
    if "Live" in secondary_types or primary_type == "Live":
        return "Live"
    if "Compilation" in secondary_types or primary_type == "Compilation":
        return "Compilation"
    if "Remix" in secondary_types or primary_type == "Remix":
        return "Remix"
    if "Soundtrack" in secondary_types or primary_type == "Soundtrack":
        return "Soundtrack"
    if "Interview" in secondary_types or primary_type == "Interview":
        return "Interview"
    if "Spokenword" in secondary_types or primary_type == "Spokenword":
        return "Spokenword"
    if "Audiobook" in secondary_types or primary_type == "Audiobook":
        return "Audiobook"
    if "Mixtape" in secondary_types or primary_type == "Mixtape":
        return "Mixtape"
    if "Demo" in secondary_types or primary_type == "Demo":
        return "Demo"
    if "DJ-mix" in secondary_types or primary_type == "DJ-mix":
        return "DJ-mix"
    if primary_type == "Album":
        return "Album"
    if primary_type == "EP":
        return "EP"
    if primary_type == "Single":
        return "Single"
    if primary_type == "Broadcast":
        return "Broadcast"
    if primary_type == "Other":
        return "Other"
    return "Unknown"
