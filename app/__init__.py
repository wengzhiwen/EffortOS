import os

from flask import Flask

from app.config import config_by_name


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder="templates",
        static_folder="static",
    )
    app.config.from_object(config_by_name[config_name])

    # 确保 instance 目录存在
    os.makedirs(app.instance_path, exist_ok=True)

    # 初始化 MongoDB
    from mongoengine import connect

    mongo_settings = app.config["MONGODB_SETTINGS"]
    connect(
        db=mongo_settings["db"],
        host=mongo_settings["host"],
        port=mongo_settings["port"],
        alias="default",
    )

    # 注册蓝图
    from app.blueprints.pages.routes import pages_bp
    from app.blueprints.activities.routes import activities_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(activities_bp, url_prefix="/api")

    return app
