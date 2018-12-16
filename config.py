from os import environ


class Config():
    ENVIROMENT = environ.get('NUMU_ENV', 'development')
    SECRET_KEY = environ.get('SECRET_KEY', 'numutracker_secret_key')
    SQLALCHEMY_DATABASE_URI = environ.get('DB_URI', 'postgresql://numu:numu@localhost/numu')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
