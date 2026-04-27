from flask import request

from app.models.user import User


def get_authenticated_user():
    """从请求中获取已认证的用户。支持 Bearer token 和 cookie。"""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if not token:
        token = request.cookies.get("session_token", "").strip()
    if not token:
        return None
    return User.objects(session_token=token).first()


def require_user():
    """要求用户已认证，返回 (user, error_response)。"""
    from flask import jsonify

    user = get_authenticated_user()
    if not user:
        return None, (jsonify({"code": 401, "message": "请先登录", "data": None}), 401)
    return user, None


def user_filter(qs):
    """按当前用户过滤查询集（无用户时返回全集）。"""
    user = get_authenticated_user()
    return qs.filter(user=user) if user else qs
