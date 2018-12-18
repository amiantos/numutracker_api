from os import environ


class Config():
    ENVIROMENT = environ.get('NUMU_ENV', 'development')
    SECRET_KEY = environ.get('SECRET_KEY', 'numutracker_secret_key')
    APIV2_KEY = environ.get('NUMU_V2_API_KEY')
    LAST_FM_API_KEY = environ.get('LAST_FM_API_KEY')
    SQLALCHEMY_DATABASE_URI = environ.get('DB_URI', 'postgresql://numu:numu@localhost/numu')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
