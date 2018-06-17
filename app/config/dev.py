# Copy this file to prod.py for production environments.
import os

NUMU_ENVIRONMENT = "Development"

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = "postgresql://numu@postgres:5432/numu"
SQLALCHEMY_TRACK_MODIFICATIONS = False

SECRET_KEY = "65c9cfc302b643b2d0a20d44f404314a00ce54e423ae6571"

DEBUG = True

APIV2_KEY = 'none'

LAST_FM_API_KEY = 'none'
