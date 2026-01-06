import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-prod"
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or "postgresql://archive_admin:change_this_secure_password@db:5432/archive_db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER") or "/data/docs"
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH") or 104857600)
    ALLOWED_EXTENSIONS = set(os.environ.get("ALLOWED_EXTENSIONS", "").split(","))

    SEARCH_RESULTS_PER_PAGE = int(os.environ.get("SEARCH_RESULTS_PER_PAGE") or 25)
    AUDIT_LOG_ENABLED = os.environ.get("AUDIT_LOG_ENABLED", "true").lower() == "true"

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    FLASK_ENV = "development"
    DEBUG = True


class ProductionConfig(Config):
    FLASK_ENV = "production"
    DEBUG = False

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
