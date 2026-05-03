from flask import Blueprint, redirect, render_template, request, url_for

from app.utils.auth import get_authenticated_user

pages_bp = Blueprint("pages", __name__)

# 不需要登录的页面
_PUBLIC_PAGES = {"pages.login", "pages.help_page", "pages.about", "pages.landing"}


def _require_login_for(template, **kwargs):
    """检查登录状态：已登录返回模板，未登录重定向到落地页或登录页。"""
    user = get_authenticated_user()
    if not user:
        # 如果是浏览器直接访问（非 API），重定向到落地页
        if request.accept_mimetypes.accept_html:
            return redirect(url_for("pages.landing"))
        return redirect(url_for("pages.login"))
    return render_template(template, **kwargs)


@pages_bp.route("/")
def index():
    """首页：未登录显示落地页，已登录显示仪表盘。"""
    user = get_authenticated_user()
    if not user:
        return render_template("landing.html")
    return render_template("index.html")


@pages_bp.route("/landing")
def landing():
    """落地页。"""
    return render_template("landing.html")


@pages_bp.route("/activities")
def activities():
    """活动列表（需登录）。"""
    return _require_login_for("activities.html")


@pages_bp.route("/activities/<activity_id>")
def activity_detail(activity_id):
    """活动详情（需登录）。"""
    return _require_login_for("activity_detail.html", activity_id=activity_id)


@pages_bp.route("/settings")
def settings():
    """参数设置（需登录）。"""
    return _require_login_for("settings.html")


@pages_bp.route("/ai")
def ai():
    """AI 教练（需登录）。"""
    return _require_login_for("ai.html")


@pages_bp.route("/login")
def login():
    """登录页：已登录用户直接跳转仪表盘。"""
    user = get_authenticated_user()
    if user:
        return redirect(url_for("pages.index"))
    return render_template("login.html")


@pages_bp.route("/profile")
def profile():
    """用户资料（需登录）。"""
    return _require_login_for("profile.html")


@pages_bp.route("/gear")
def gear():
    """装备管理（需登录）。"""
    return _require_login_for("gear.html")


@pages_bp.route("/wellness")
def wellness():
    """Wellness 日常追踪（需登录）。"""
    return _require_login_for("wellness.html")


@pages_bp.route("/help")
def help_page():
    """帮助页（公开）。"""
    return render_template("help.html")


@pages_bp.route("/about")
def about():
    """关于页（公开）。"""
    return render_template("about.html")
