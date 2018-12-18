from os import environ


class Config():
    ENVIROMENT = environ.get('NUMU_ENV', 'development')
    APIV2_KEY = environ.get('NUMU_V2_API_KEY')
    LAST_FM_API_KEY = environ.get('LAST_FM_API_KEY')
    SECRET_KEY = environ.get('SECRET_KEY', 'VbRkVKHw0rEBaVayLc6n1P34bIk91oN6')
    SQLALCHEMY_DATABASE_URI = environ.get('DB_URI', 'postgresql://numu:numu@localhost/numu')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
