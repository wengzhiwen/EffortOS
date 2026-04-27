from datetime import datetime

from flask import Blueprint, jsonify, request

from app.blueprints.auth.routes import require_user
from app.models.athlete_settings import AthleteParams
from app.services.params_service import mark_activities_for_recalc, save_params

params_bp = Blueprint("params", __name__)


def _serialize_params(params):
    """将 AthleteParams 序列化为字典。"""
    if not params:
        return None
    return {
        "id": str(params.id),
        "effective_date": params.effective_date.strftime("%Y-%m-%d"),
        "ftp": params.ftp,
        "cycling_lthr": params.cycling_lthr,
        "running_lthr": params.running_lthr,
        "walking_lthr": params.walking_lthr,
        "max_heart_rate": params.max_heart_rate,
        "weight": params.weight,
        "hr_zones": params.get_hr_zones("cycling"),
        "power_zones": params.get_power_zones(),
    }


@params_bp.route("/params", methods=["POST"])
def create_params():
    """保存运动员参数。"""
    user, err = require_user()
    if err:
        return err

    data = request.get_json()
    if not data or "effective_date" not in data:
        return jsonify({"code": 400, "message": "缺少 effective_date", "data": None}), 400

    try:
        effective_date = datetime.fromisoformat(data["effective_date"].replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return jsonify({"code": 400, "message": "日期格式错误", "data": None}), 400

    params_data = {
        "effective_date": effective_date,
        "ftp": data.get("ftp"),
        "cycling_lthr": data.get("cycling_lthr"),
        "running_lthr": data.get("running_lthr"),
        "walking_lthr": data.get("walking_lthr"),
        "max_heart_rate": data.get("max_heart_rate"),
        "weight": data.get("weight"),
    }

    # 绑定用户
    params = save_params(user, params_data)

    # 标记受影响的活动需要重算
    if params.effective_date:
        mark_activities_for_recalc(user, params.effective_date)

    return jsonify(
        {
            "code": 200,
            "message": "保存成功",
            "data": _serialize_params(params),
        }
    )


@params_bp.route("/params/latest", methods=["GET"])
def get_latest_params():
    """获取当前生效的参数。"""
    from app.blueprints.auth.routes import _get_authenticated_user as _get_user

    current_user = _get_user()
    qs = AthleteParams.objects()
    if current_user:
        qs = qs.filter(user=current_user)
    params = qs.order_by("-effective_date").first()
    return jsonify(
        {
            "code": 200,
            "message": "ok",
            "data": _serialize_params(params),
        }
    )


@params_bp.route("/params/history", methods=["GET"])
def get_params_history():
    """获取参数变更历史。"""
    from app.blueprints.auth.routes import _get_authenticated_user as _get_user

    current_user = _get_user()
    qs = AthleteParams.objects()
    if current_user:
        qs = qs.filter(user=current_user)
    params_list = qs.order_by("-effective_date").limit(20)
    return jsonify(
        {
            "code": 200,
            "message": "ok",
            "data": [_serialize_params(p) for p in params_list],
        }
    )
