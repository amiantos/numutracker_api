from datetime import datetime

import pytz

from app import app as numu_app
from pynamodb.attributes import (BinaryAttribute, BooleanAttribute,
                                 UnicodeAttribute, UTCDateTimeAttribute)
from pynamodb.indexes import AllProjection, GlobalSecondaryIndex
from pynamodb.models import Model

utc_tz = pytz.timezone('UTC')


# --------------------------------------
# User
# --------------------------------------

class EmailIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = 'email-index'
        read_capacity_units = 1
        write_capacity_units = 1
        projection = AllProjection()
    email = UnicodeAttribute(hash_key=True)


class iCloudIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = 'icloud-index'
        read_capacity_units = 1
        write_capacity_units = 1
        projection = AllProjection()
    icloud = UnicodeAttribute(hash_key=True)


class User(Model):
    class Meta:
        table_name = numu_app.config.get('USERS_TABLE')
    uuid = UnicodeAttribute(hash_key=True)
    email = UnicodeAttribute(null=True)
    password = BinaryAttribute(null=True)
    icloud = UnicodeAttribute(null=True)
    email_index = EmailIndex()
    icloud_index = iCloudIndex()

    date_joined = UTCDateTimeAttribute(default=datetime.now(utc_tz))

    # Filter Settings
    album = BooleanAttribute(default=True)
    single = BooleanAttribute(default=True)
    ep = BooleanAttribute(default=True)
    live = BooleanAttribute(default=False)
    soundtrack = BooleanAttribute(default=False)
    remix = BooleanAttribute(default=False)
    other = BooleanAttribute(default=False)
