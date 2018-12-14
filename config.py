from os import environ


class Config():
    ENVIROMENT = None
    SECRET_KEY = environ.get('SECRET_KEY', 'numutracker_secret_key')


class Development(Config):
    ENVIROMENT = "development"

    USERS_TABLE = "numu_users-dev"


class Production(Config):
    ENVIROMENT = "production"

    USERS_TABLE = "numu_users"
