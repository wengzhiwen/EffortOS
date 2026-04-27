import os
import secrets

from flask import Blueprint, jsonify, request

from app.models.user import User
from app.models.verification_code import VerificationCode

auth_bp = Blueprint("auth", __name__)


def _get_authenticated_user():
    """从请求中获取已认证的用户。支持 Bearer token 和 cookie。"""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if not token:
        token = request.cookies.get("session_token", "").strip()
    if not token:
        return None
    return User.objects(session_token=token).first()


def require_user():
    """要求用户已认证，返回 (user, error_response)。"""
    user = _get_authenticated_user()
    if not user:
        return None, (jsonify({"code": 401, "message": "请先登录", "data": None}), 401)
    return user, None


@auth_bp.route("/auth/request-code", methods=["POST"])
def request_code():
    """请求邮箱验证码。"""
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()

    if not email or "@" not in email:
        return jsonify({"code": 400, "message": "请输入有效的邮箱地址", "data": None}), 400

    # 生成验证码
    vc = VerificationCode.create_for_email(email)

    # 开发环境：在日志中显示验证码
    test_hole = os.environ.get("TEST_HOLE")
    if test_hole:
        print(f"[DEV] 验证码 for {email}: {vc.code}")

    # TODO: 生产环境发送邮件
    # 目前开发阶段直接返回验证码（仅开发/测试环境）
    is_dev = os.environ.get("FLASK_ENV") == "development"
    from flask import current_app
    expose_code = is_dev or current_app.config.get("TESTING")

    return jsonify({
        "code": 200,
        "message": "验证码已发送",
        "data": {"code": vc.code} if expose_code else None,
    })


@auth_bp.route("/auth/verify", methods=["POST"])
def verify_code():
    """验证码登录/注册。"""
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    code = (data.get("code") or "").strip()

    if not email or not code:
        return jsonify({"code": 400, "message": "请输入邮箱和验证码", "data": None}), 400

    # 查找最新的未使用验证码
    vc = VerificationCode.objects(email=email, used_at=None).order_by("-created_at").first()
    if not vc or not secrets.compare_digest(vc.code, code) or not vc.is_valid():
        return jsonify({"code": 400, "message": "验证码无效或已过期", "data": None}), 400

    # 测试后门
    test_hole = os.environ.get("TEST_HOLE")
    if test_hole and code == test_hole:
        pass  # 允许通过
    elif not secrets.compare_digest(vc.code, code):
        return jsonify({"code": 400, "message": "验证码错误", "data": None}), 400

    vc.mark_used()

    # 查找或创建用户
    user = User.objects(email=email).first()
    if not user:
        nickname = email.split("@")[0]
        user = User(email=email, nickname=nickname)

    token = user.generate_session_token()

    response = jsonify({
        "code": 200,
        "message": "登录成功",
        "data": {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "nickname": user.nickname,
            },
            "token": token,
        },
    })
    response.set_cookie("session_token", token, httponly=True, max_age=86400, samesite="Lax")
    return response


@auth_bp.route("/auth/logout", methods=["POST"])
def logout():
    """登出。"""
    user = _get_authenticated_user()
    if user:
        user.clear_session_token()

    response = jsonify({"code": 200, "message": "已登出", "data": None})
    response.delete_cookie("session_token")
    return response


@auth_bp.route("/auth/me", methods=["GET"])
def me():
    """获取当前用户信息。"""
    user, err = require_user()
    if err:
        return err

    return jsonify({
        "code": 200,
        "message": "ok",
        "data": {
            "id": str(user.id),
            "email": user.email,
            "nickname": user.nickname,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
    })


@auth_bp.route("/auth/profile", methods=["PUT"])
def update_profile():
    """更新用户资料。"""
    user, err = require_user()
    if err:
        return err

    data = request.get_json() or {}
    nickname = (data.get("nickname") or "").strip()

    if not nickname:
        return jsonify({"code": 400, "message": "昵称不能为空", "data": None}), 400

    user.nickname = nickname[:50]
    user.save()

    return jsonify({
        "code": 200,
        "message": "更新成功",
        "data": {
            "id": str(user.id),
            "email": user.email,
            "nickname": user.nickname,
        },
    })
