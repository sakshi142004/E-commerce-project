import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Security
    SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-secret-key")

    # Database selection is environment-driven and safe by default:
    # - Local development can use the live database only when DATABASE_URL is
    #   pasted into the local .env file.
    # - Railway/Render should keep using their platform DATABASE_URL variable.
    # - If DATABASE_URL is missing, the app falls back to local SQLite.
    # Never hardcode a real database URL in this file.
    db_url = os.environ.get("DATABASE_URL")

    if db_url:
        # Some platforms expose postgres://, but SQLAlchemy expects postgresql://.
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)

        SQLALCHEMY_DATABASE_URI = db_url
    else:
        # Safe local-only fallback used when no DATABASE_URL is configured.
        SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "instance/site.db")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File uploads
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static/images")

    # Cloudinary
    CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME") or "dhjl5plm8"
    CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY") or "881392445818876"
    CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET") or "wJcwQke-UHL4YQAAskXSYDFNiTE"
