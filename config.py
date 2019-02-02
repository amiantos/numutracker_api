import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    ENVIROMENT = os.getenv("NUMU_ENV", "development")
    NUMU_V2_API_KEY = os.getenv("NUMU_V2_API_KEY")
    LAST_FM_API_KEY = os.getenv("LAST_FM_API_KEY")
    SECRET_KEY = os.getenv("SECRET_KEY", "VbRkVKHw0rEBaVayLc6n1P34bIk91oN6")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DB_URI", "postgresql://numu:numu@localhost/numu"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DO_ACCESS_KEY = os.getenv("DO_ACCESS_KEY")
    DO_SECRET_KEY = os.getenv("DO_SECRET_KEY")


class Test(Config):
    ENVIROMENT = "test"
    SQLALCHEMY_DATABASE_URI = "postgresql://numu:numu@postgres/test"
