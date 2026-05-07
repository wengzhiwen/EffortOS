import logging
import os

from flask import Flask, jsonify, render_template, request

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
    from app.blueprints.activities.routes import activities_bp
    from app.blueprints.ai.routes import ai_bp
    from app.blueprints.auth.routes import auth_bp
    from app.blueprints.dashboard.routes import dashboard_bp
    from app.blueprints.pages.routes import pages_bp
    from app.blueprints.params.routes import params_bp
    from app.blueprints.wellness.routes import wellness_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(activities_bp, url_prefix="/api")
    app.register_blueprint(params_bp, url_prefix="/api")
    app.register_blueprint(ai_bp, url_prefix="/api")
    app.register_blueprint(dashboard_bp, url_prefix="/api")
    app.register_blueprint(wellness_bp, url_prefix="/api")

    # API 速率限制
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "500 per hour"],
        storage_uri="memory://",
    )

    # 安全响应头
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    # 统一错误处理
    @app.errorhandler(404)
    def handle_404(error):
        if request.path.startswith("/api/"):
            return jsonify({"code": 404, "message": "资源不存在", "data": None}), 404
        return render_template("error.html", code=404, message="页面不存在"), 404

    @app.errorhandler(500)
    def handle_500(error):
        logger.error("内部错误: %s", error, exc_info=True)
        if request.path.startswith("/api/"):
            return jsonify({"code": 500, "message": "服务器内部错误", "data": None}), 500
        return render_template("error.html", code=500, message="服务器内部错误"), 500

    return app
