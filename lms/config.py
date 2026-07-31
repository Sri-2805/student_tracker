import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_NAME = os.environ.get("DB_NAME", "lms_tracker")

    # If no MySQL password or explicit flag is set, fall back to a local SQLite DB
    if DB_PASSWORD == "" and os.environ.get("USE_SQLITE", "") in ("", "1", "true", "True"):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'lms_dev.db')}"
    else:
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}

    # Attendance / analytics thresholds
    ATTENDANCE_ALERT_THRESHOLD = 75.0   # percent
    GRADE_ALERT_THRESHOLD = 50.0        # percent

    EXPORT_DIR = os.path.join(BASE_DIR, "exports")
