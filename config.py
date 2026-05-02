import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
class Config:
    # 🔐 Security
    SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-secret-key")

    # 🗄️ Database (Render PostgreSQL fix included)
    db_url = os.environ.get("DATABASE_URL")

    if db_url:
        # Fix for Render (postgres:// → postgresql://)
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)

        SQLALCHEMY_DATABASE_URI = db_url
    else:
        # Local fallback
        SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "instance/site.db")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 📁 File uploads
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static/images")

    # ☁️ Cloudinary
    # ☁️ Cloudinary
    CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME") or "dhjl5plm8"
    CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY") or "881392445818876"
    CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET") or "wJcwQke-UHL4YQAAskXSYDFNiTE"