import uuid

from app import bcrypt
from models import User


# --------------------------------------
# User
# --------------------------------------

def insert_user(email=None, icloud=None, password=None):
    user_uuid = uuid.uuid4().hex
    hashed_password = None
    if password:
        hashed_password = bcrypt.generate_password_hash(password)

    new_user = User(
        user_uuid,
        password=hashed_password,
        icloud=icloud,
        email=email)
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
