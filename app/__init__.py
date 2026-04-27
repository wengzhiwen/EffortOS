import logging
import os

from flask import Flask, jsonify

from app.config import config_by_name

logger = logging.getLogger(__name__)


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
    from app.blueprints.params.routes import params_bp
    from app.blueprints.ai.routes import ai_bp
    from app.blueprints.auth.routes import auth_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(activities_bp, url_prefix="/api")
    app.register_blueprint(params_bp, url_prefix="/api")
    app.register_blueprint(ai_bp, url_prefix="/api")

    # 安全响应头
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    # 统一错误处理
    @app.errorhandler(400)
    @app.errorhandler(404)
    @app.errorhandler(422)
    def handle_client_error(error):
        return jsonify({"code": error.code, "message": error.description, "data": None}), error.code

    @app.errorhandler(500)
    def handle_server_error(error):
        logger.error("内部错误: %s", error, exc_info=True)
        return jsonify({"code": 500, "message": "服务器内部错误", "data": None}), 500

    return app
