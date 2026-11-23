
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

CA_FILE = BASE_DIR / "certs" / "isrgrootx1.pem"

class Config:

    SECRET_KEY = os.getenv("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT", "4000")),
        database=os.getenv("MYSQL_DB"),
    )

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "connect_args": {
            "ssl_ca": str(CA_FILE),
            "ssl_verify_cert": True,
            "ssl_verify_identity": True,
            "connect_timeout": 15,
        },
    }

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", os.getenv("MAIL_USERNAME"))

    UPLOAD_FOLDER = str(BASE_DIR / "static" / "uploads" / "profile")
    RESUME_UPLOAD_FOLDER = str(BASE_DIR / "static" / "uploads" / "resumes")
    SOCIAL_UPLOAD_FOLDER = str(BASE_DIR / "static" / "uploads" / "social")

    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
