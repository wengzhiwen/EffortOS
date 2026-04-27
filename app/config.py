import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    MONGODB_SETTINGS = {
        "host": os.environ.get("MONGODB_HOST", "localhost"),
        "port": int(os.environ.get("MONGODB_PORT", 27017)),
        "db": os.environ.get("MONGODB_DB", "effortos"),
    }
    UPLOAD_FOLDER = os.environ.get(
        "UPLOAD_FOLDER",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "instance", "uploads"),
    )
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    MONGODB_SETTINGS = {
        "host": os.environ.get("MONGODB_HOST", "localhost"),
        "port": int(os.environ.get("MONGODB_PORT", 27017)),
        "db": "effortos_test",
    }


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
