import os
import secrets

from flask import Blueprint, jsonify, request

from app.models.user import User
from app.models.verification_code import VerificationCode
from app.services.i18n_service import t
from app.utils.auth import get_authenticated_user
from app.utils.auth import require_user as _require_user

auth_bp = Blueprint("auth", __name__)


def _get_authenticated_user():
    """兼容旧调用方的委托函数。"""
    return get_authenticated_user()


def require_user():
    """兼容旧调用方的委托函数。"""
    return _require_user()


@auth_bp.route("/auth/request-code", methods=["POST"])
def request_code():
    """请求邮箱验证码。"""
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()

    if not email or "@" not in email:
        return jsonify({"code": 400, "message": t("auth.invalid_email"), "data": None}), 400

    vc = VerificationCode.create_for_email(email)

    test_hole = os.environ.get("TEST_HOLE") if os.environ.get("FLASK_ENV") == "testing" else None
    if test_hole:
        print(f"[DEV] 验证码 for {email}: {vc.code}")

    is_dev = os.environ.get("FLASK_ENV") == "development"
    from flask import current_app

    expose_code = is_dev or current_app.config.get("TESTING")

    return jsonify(
        {
            "code": 200,
            "message": t("auth.code_sent"),
            "data": {"code": vc.code} if expose_code else None,
        }
    )


@auth_bp.route("/auth/verify", methods=["POST"])
def verify_code():
    """验证码登录/注册。"""
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    code = (data.get("code") or "").strip()

    if not email or not code:
        return jsonify({"code": 400, "message": t("auth.email_code_required"), "data": None}), 400

    test_hole = os.environ.get("TEST_HOLE") if os.environ.get("FLASK_ENV") == "testing" else None
    if test_hole and code == test_hole:
        vc = VerificationCode.objects(email=email).order_by("-created_at").first()
        if not vc:
            return jsonify({"code": 400, "message": t("auth.get_code_first"), "data": None}), 400
    else:
        vc = VerificationCode.objects(email=email, used_at=None).order_by("-created_at").first()
        if not vc or not secrets.compare_digest(vc.code, code) or not vc.is_valid():
            return jsonify({"code": 400, "message": t("auth.code_invalid"), "data": None}), 400

    vc.mark_used()

    user = User.objects(email=email).first()
    if not user:
        nickname = email.split("@")[0]
        user = User(email=email, nickname=nickname)

    token = user.generate_session_token()

    response = jsonify(
        {
            "code": 200,
            "message": t("auth.login_success"),
            "data": {
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "nickname": user.nickname,
                },
                "token": token,
            },
        }
    )
    response.set_cookie("session_token", token, httponly=True, max_age=86400, samesite="Lax")
    return response


@auth_bp.route("/auth/logout", methods=["POST"])
def logout():
    """登出。"""
    user = get_authenticated_user()
    if user:
        user.clear_session_token()

    response = jsonify({"code": 200, "message": t("auth.logged_out"), "data": None})
    response.delete_cookie("session_token")
    return response


@auth_bp.route("/auth/me", methods=["GET"])
def me():
    """获取当前用户信息。"""
    user, err = _require_user()
    if err:
        return err

    return jsonify(
        {
            "code": 200,
            "message": "ok",
            "data": {
                "id": str(user.id),
                "email": user.email,
                "nickname": user.nickname,
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            },
        }
    )


@auth_bp.route("/auth/profile", methods=["PUT"])
def update_profile():
    """更新用户资料。"""
    user, err = _require_user()
    if err:
        return err

    data = request.get_json() or {}
    nickname = (data.get("nickname") or "").strip()

    if not nickname:
        return jsonify({"code": 400, "message": t("auth.nickname_required"), "data": None}), 400

    user.nickname = nickname[:50]
    user.save()

    return jsonify(
        {
            "code": 200,
            "message": t("auth.update_success"),
            "data": {
                "id": str(user.id),
                "email": user.email,
                "nickname": user.nickname,
            },
        }
    )
