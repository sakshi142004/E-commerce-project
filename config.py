import os


class Config:
    SECRET_KEY = '95c32ec77c8d69db8b76e50fab0d6a9d'

    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:root@localhost/belt_paradise'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static/images")

    CLOUDINARY_CLOUD_NAME = "dhjl5plm8"
    CLOUDINARY_API_KEY = "881392445818876"
    CLOUDINARY_API_SECRET = "wJcwQke-UHL4YQAAskXSYDFNiTE"

