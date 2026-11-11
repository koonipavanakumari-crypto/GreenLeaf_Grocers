
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "greenleaf_secret_key_2026"

    SQLALCHEMY_DATABASE_URI = (
        "sqlite:///" + os.path.join(
            BASE_DIR, "instance", "greenleaf.db"
        )
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

