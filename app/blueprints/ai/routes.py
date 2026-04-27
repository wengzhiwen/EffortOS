from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request

from app.blueprints.auth.routes import require_user
from app.models.activity import Activity
from app.models.athlete_settings import AthleteParams
from app.services.llm_service import generate_suggestion, generate_weekly_report
from app.services.metrics_service import calc_daily_tss, calc_pmc

ai_bp = Blueprint("ai", __name__)


def _get_current_context(user=None):
    """获取当前训练状态上下文。"""
    today = datetime.now(timezone.utc)
    start = (today - timedelta(days=60)).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")

    qs = Activity.objects(
        start_time__gte=start,
        start_time__lte=end + "T23:59:59",
    )
    if user:
        qs = qs.filter(user=user)
    activities = list(qs)
    daily = calc_daily_tss(activities)
    pmc_data = calc_pmc(daily, start, end)
    latest = pmc_data[-1] if pmc_data else {"ctl": 0, "atl": 0, "tsb": 0}

    params_qs = AthleteParams.objects()
    if user:
        params_qs = params_qs.filter(user=user)
    params = params_qs.order_by("-effective_date").first()
    params_dict = {}
    if params:
        params_dict = {
            "ftp": params.ftp,
            "cycling_lthr": params.cycling_lthr,
            "running_lthr": params.running_lthr,
            "max_heart_rate": params.max_heart_rate,
            "weight": params.weight,
        }

    return latest, daily, params_dict


@ai_bp.route("/ai/weekly-report", methods=["POST"])
def weekly_report():
    """生成训练周报。"""
    user, err = require_user()
    if err:
        return err

    try:
        latest_pmc, daily_tss, params = _get_current_context(user)
    except Exception as e:
        return jsonify({"code": 500, "message": f"获取数据失败: {str(e)}", "data": None}), 500

    # 获取本周活动
    today = datetime.now(timezone.utc)
    week_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
    week_activities = Activity.objects(
        start_time__gte=week_start,
        user=user,
    ).order_by("start_time")

    activities_data = []
    for a in week_activities:
        act_dict = {
            "name": a.name,
            "activity_type": a.activity_type,
            "start_time": a.start_time.isoformat(),
            "data_summary": {},
            "computed_metrics": {},
        }
        if a.data_summary:
            act_dict["data_summary"] = {"duration_seconds": a.data_summary.duration_seconds}
        if a.computed_metrics:
            act_dict["computed_metrics"] = {"tss": a.computed_metrics.tss}
        activities_data.append(act_dict)

    try:
        report = generate_weekly_report(activities_data, latest_pmc, params)
    except ValueError as e:
        return jsonify({"code": 400, "message": str(e), "data": None}), 400
    except Exception as e:
        return jsonify({"code": 500, "message": f"生成失败: {str(e)}", "data": None}), 500

    return jsonify({
        "code": 200,
        "message": "ok",
        "data": {
            "report": report,
            "week_activities": len(activities_data),
            "ctl": latest_pmc["ctl"],
            "atl": latest_pmc["atl"],
            "tsb": latest_pmc["tsb"],
        },
    })


@ai_bp.route("/ai/suggestion", methods=["POST"])
def suggestion():
    """获取个性化训练建议。"""
    user, err = require_user()
    if err:
        return err

    data = request.get_json() or {}
    question = data.get("question", "")

    try:
        latest_pmc, daily_tss, params = _get_current_context(user)
    except Exception as e:
        return jsonify({"code": 500, "message": f"获取数据失败: {str(e)}", "data": None}), 500

    # 最近 7 天 TSS
    today = datetime.now(timezone.utc)
    recent_tss = []
    for i in range(6, -1, -1):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        recent_tss.append(daily_tss.get(date, 0))

    try:
        advice = generate_suggestion(latest_pmc, recent_tss, params, question)
    except ValueError as e:
        return jsonify({"code": 400, "message": str(e), "data": None}), 400
    except Exception as e:
        return jsonify({"code": 500, "message": f"生成失败: {str(e)}", "data": None}), 500

    return jsonify({
        "code": 200,
        "message": "ok",
        "data": {
            "suggestion": advice,
            "ctl": latest_pmc["ctl"],
            "atl": latest_pmc["atl"],
            "tsb": latest_pmc["tsb"],
        },
    })
