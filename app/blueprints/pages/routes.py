from flask import Blueprint, render_template

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def index():
    return render_template("index.html")


@pages_bp.route("/activities")
def activities():
    return render_template("activities.html")


@pages_bp.route("/activities/<activity_id>")
def activity_detail(activity_id):
    return render_template("activity_detail.html", activity_id=activity_id)


@pages_bp.route("/settings")
def settings():
    return render_template("settings.html")


@pages_bp.route("/ai")
def ai():
    return render_template("ai.html")


@pages_bp.route("/login")
def login():
    return render_template("login.html")


@pages_bp.route("/profile")
def profile():
    return render_template("profile.html")


@pages_bp.route("/help")
def help_page():
    return render_template("help.html")
