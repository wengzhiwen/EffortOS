from datetime import datetime

from flask import Blueprint, jsonify, request

from app.models.athlete_settings import AthleteParams
from app.services.i18n_service import t
from app.services.params_service import mark_activities_for_recalc, save_params
from app.utils.auth import require_user, user_filter

params_bp = Blueprint("params", __name__)


def _clamp_int(val, lo, hi):
    if val is None:
        return None
    try:
        v = int(val)
    except (ValueError, TypeError):
        return None
    return max(lo, min(hi, v))


def _clamp_float(val, lo, hi):
    if val is None:
        return None
    try:
        v = float(val)
    except (ValueError, TypeError):
        return None
    return max(lo, min(hi, v))


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
        return jsonify({"code": 400, "message": t("api.missing_effective_date"), "data": None}), 400

    try:
        effective_date = datetime.fromisoformat(data["effective_date"].replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return jsonify({"code": 400, "message": t("api.date_format_error"), "data": None}), 400

    params_data = {
        "effective_date": effective_date,
        "ftp": _clamp_int(data.get("ftp"), 50, 600),
        "cycling_lthr": _clamp_int(data.get("cycling_lthr"), 60, 220),
        "running_lthr": _clamp_int(data.get("running_lthr"), 60, 220),
        "walking_lthr": _clamp_int(data.get("walking_lthr"), 60, 220),
        "max_heart_rate": _clamp_int(data.get("max_heart_rate"), 60, 250),
        "weight": _clamp_float(data.get("weight"), 20, 300),
    }

    params = save_params(user, params_data)

    if params.effective_date:
        mark_activities_for_recalc(user, params.effective_date)

    return jsonify(
        {
            "code": 200,
            "message": t("api.save_success"),
            "data": _serialize_params(params),
        }
    )


@params_bp.route("/params/latest", methods=["GET"])
def get_latest_params():
    """获取当前生效的参数。"""
    qs = user_filter(AthleteParams.objects())
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
    qs = user_filter(AthleteParams.objects())
    params_list = qs.order_by("-effective_date").limit(20)
    return jsonify(
        {
            "code": 200,
            "message": "ok",
            "data": [_serialize_params(p) for p in params_list],
        }
    )


@params_bp.route("/params/<params_id>", methods=["PUT"])
def update_params(params_id):
    """编辑历史参数记录。"""
    user, err = require_user()
    if err:
        return err

    params = AthleteParams.objects(id=params_id, user=user).first()
    if not params:
        return jsonify({"code": 404, "message": t("api.params_not_found"), "data": None}), 404

    data = request.get_json()
    if not data:
        return jsonify({"code": 400, "message": t("api.missing_request_body"), "data": None}), 400

    if "effective_date" in data:
        try:
            params.effective_date = datetime.fromisoformat(data["effective_date"].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return jsonify({"code": 400, "message": t("api.date_format_error"), "data": None}), 400

    if "ftp" in data:
        params.ftp = _clamp_int(data["ftp"], 50, 600)
    if "cycling_lthr" in data:
        params.cycling_lthr = _clamp_int(data["cycling_lthr"], 60, 220)
    if "running_lthr" in data:
        params.running_lthr = _clamp_int(data["running_lthr"], 60, 220)
    if "walking_lthr" in data:
        params.walking_lthr = _clamp_int(data["walking_lthr"], 60, 220)
    if "max_heart_rate" in data:
        params.max_heart_rate = _clamp_int(data["max_heart_rate"], 60, 250)
    if "weight" in data:
        params.weight = _clamp_float(data["weight"], 20, 300)

    params.save()
    mark_activities_for_recalc(user, params.effective_date)

    return jsonify({"code": 200, "message": t("api.updated"), "data": _serialize_params(params)})


@params_bp.route("/params/<params_id>", methods=["DELETE"])
def delete_params(params_id):
    """删除历史参数记录。"""
    user, err = require_user()
    if err:
        return err

    params = AthleteParams.objects(id=params_id, user=user).first()
    if not params:
        return jsonify({"code": 404, "message": t("api.params_not_found"), "data": None}), 404

    effective_date = params.effective_date
    params.delete()

    # 删除后重算受影响的活动
    mark_activities_for_recalc(user, effective_date)

    return jsonify({"code": 200, "message": t("api.deleted"), "data": None})


@params_bp.route("/params/recalc-status", methods=["GET"])
def get_recalc_status():
    """获取数据重算进度。"""
    from app.services.params_service import get_recalc_status as _get_status
    from app.utils.auth import get_authenticated_user

    user = get_authenticated_user()
    if not user:
        return jsonify({"code": 200, "message": "ok", "data": {"total": 0, "done": 0, "running": False}})

    status = _get_status(user.id)
    return jsonify({"code": 200, "message": "ok", "data": status})
