import json
from datetime import datetime

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
