import uuid
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from app import bcrypt, app as numu_app
from models import User


USERS_TABLE = numu_app.config.get('USERS_TABLE')

dbclient = boto3.client('dynamodb')
dbresource = boto3.resource('dynamodb')


def insert_user(email=None, icloud=None, password=None):
    user_uuid = uuid.uuid4().hex
    hashed_password = None
    if password:
        hashed_password = bcrypt.generate_password_hash(password)

    new_user = User(user_uuid, password=hashed_password, icloud=icloud, email=email)
    new_user.save()

    return new_user


def get_user_by_email(email):
    users = User.email_index.query(email)
    for user in users:
        return user
    return None


def get_user_by_icloud(icloud):
    users = User.icloud_index.query(icloud)
    for user in users:
        return user
    return None
