import os

NUMU_ENVIRONMENT = "Development"

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = "postgresql://numu@localhost:5432/numu"
