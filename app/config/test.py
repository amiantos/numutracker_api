import os

NUMU_ENVIRONMENT = "Testing"

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = "postgresql://numu@postgres:5432/test"
SQLALCHEMY_TRACK_MODIFICATIONS = False

SECRET_KEY = "65c9cfc302b643b2d0a20d44f404314a00ce54e423ae6571"

TESTING = True
