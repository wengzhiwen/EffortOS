import json
import re
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request

from app.models.activity import Activity
from app.models.athlete_settings import AthleteParams
from app.models.user import WeeklyReport
from app.services.llm_service import generate_suggestion, generate_weekly_report
from app.services.metrics_service import calc_daily_tss, calc_pmc
from app.utils.auth import require_user

ai_bp = Blueprint("ai", __name__)

_TYPE_NAMES = {
    "cycling": "骑行",
    "indoor_cycling": "室内骑行",
    "running": "跑步",
    "indoor_running": "室内跑步",
    "walking": "步行",
    "swimming": "游泳",
    "other": "其他",
}

_INTENSITY_NAMES = {
    "recovery": "恢复",
    "endurance": "有氧耐力",
    "tempo": "节奏",
    "threshold": "阈值",
    "vo2max": "VO2max",
}


def _get_current_context(user=None):
    """获取当前训练状态上下文。

    返回 (latest_pmc, daily_tss, params_dict, pmc_series)
    - latest_pmc: 最新的 CTL/ATL/TSB
    - daily_tss: 每日 TSS 字典
    - params_dict: 运动员参数
    - pmc_series: 完整 PMC 时间序列（60 天）
    """
    today = datetime.now(timezone.utc)
    start = (today - timedelta(days=60)).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")

    qs = Activity.objects(start_time__gte=start)
    if user:
        qs = qs.filter(user=user)
    # start_time 存为 naive datetime，字符串 lte 比较有兼容问题，用 gte + 内存过滤
    activities = [a for a in qs if a.start_time.strftime("%Y-%m-%d") <= end]
    daily = calc_daily_tss(activities)
    pmc_series = calc_pmc(daily, start, end)
    latest = pmc_series[-1] if pmc_series else {"ctl": 0, "atl": 0, "tsb": 0}

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

    return latest, daily, params_dict, pmc_series


def _activity_to_dict(a):
    """将 Activity 对象转为摘要字典。"""
    act_dict = {
        "name": a.name,
        "activity_type": _TYPE_NAMES.get(a.activity_type, a.activity_type),
        "start_time": a.start_time.isoformat(),
        "data_summary": {},
        "computed_metrics": {},
    }
    if a.data_summary:
        act_dict["data_summary"] = {"duration_seconds": a.data_summary.duration_seconds}
    if a.computed_metrics:
        cm = a.computed_metrics
        act_dict["computed_metrics"] = {
            "tss": cm.tss,
            "intensity_level": _INTENSITY_NAMES.get(cm.intensity_level, cm.intensity_level),
        }
    return act_dict


def _recent_history_list(user, limit=20):
    """获取用户最近 N 次训练的简明列表，供 LLM 参考。"""
    acts = Activity.objects(user=user).order_by("-start_time").limit(limit)
    rows = []
    for a in acts:
        cm = a.computed_metrics
        ds = a.data_summary
        rows.append(
            {
                "date": a.start_time.strftime("%m-%d"),
                "name": a.name,
                "type": _TYPE_NAMES.get(a.activity_type, a.activity_type),
                "duration_min": (ds.duration_seconds // 60) if ds else 0,
                "tss": cm.tss if cm else None,
                "hr_tss": cm.hr_tss if cm else None,
                "intensity": _INTENSITY_NAMES.get(cm.intensity_level, cm.intensity_level) if cm else None,
            }
        )
    return rows


@ai_bp.route("/ai/weekly-report", methods=["POST"])
def weekly_report():
    """生成训练报告（最近 7 天回顾 + 未来 7 天逐日计划）。"""
    user, err = require_user()
    if err:
        return err

    try:
        latest_pmc, daily_tss, params, pmc_series = _get_current_context(user)
    except Exception as e:
        return jsonify({"code": 500, "message": f"获取数据失败: {str(e)}", "data": None}), 500

    today = datetime.now(timezone.utc)
    today_str = today.strftime("%Y-%m-%d")

    # 最近 7 天活动（含今天）
    seven_days_ago = (today - timedelta(days=6)).strftime("%Y-%m-%d")
    recent_activities = Activity.objects(
        start_time__gte=seven_days_ago,
        user=user,
    ).order_by("start_time")
    recent_data = [_activity_to_dict(a) for a in recent_activities]

    # 判断今天是否已有训练
    has_training_today = any(a.start_time.strftime("%Y-%m-%d") == today_str for a in recent_activities)

    # 最近 7 天每日 PMC（从完整序列中截取）
    recent_pmc = []
    for entry in pmc_series:
        if entry["date"] >= seven_days_ago:
            recent_pmc.append(entry)

    # 未来 7 天日期标签：如果今天已有训练则从明天开始
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    start_offset = 1 if has_training_today else 0
    future_days = []
    for i in range(start_offset, start_offset + 7):
        d = today + timedelta(days=i)
        label = f"{d.strftime('%m-%d')} {weekday_names[d.weekday()]}"
        if i == 0:
            label += "（今天）"
        future_days.append(label)

    # 最近 20 次训练历史（供 LLM 参考复用）
    history = _recent_history_list(user)

    try:
        raw = generate_weekly_report(recent_data, recent_pmc, latest_pmc, params, future_days, today_str, history)
    except ValueError as e:
        return jsonify({"code": 400, "message": str(e), "data": None}), 400
    except Exception as e:
        return jsonify({"code": 500, "message": f"生成失败: {str(e)}", "data": None}), 500

    # 从 LLM 返回中提取 JSON
    json_match = re.search(r"\{[\s\S]*\}", raw)
    if not json_match:
        return jsonify({"code": 500, "message": "LLM 返回格式异常", "data": None}), 500
    try:
        report_data = json.loads(json_match.group())
    except json.JSONDecodeError:
        return jsonify({"code": 500, "message": "LLM 返回 JSON 解析失败", "data": None}), 500

    plan_json = json.dumps(report_data.get("plan", []), ensure_ascii=False)

    # 持久化
    user.weekly_report = WeeklyReport(
        summary=report_data.get("summary", ""),
        plan_json=plan_json,
        outlook=report_data.get("outlook", ""),
        ctl=latest_pmc["ctl"],
        atl=latest_pmc["atl"],
        tsb=latest_pmc["tsb"],
        week_activities=len(recent_data),
        generated_at=datetime.now(timezone.utc),
    )
    user.save()

    return jsonify(
        {
            "code": 200,
            "message": "ok",
            "data": {
                "summary": report_data.get("summary", ""),
                "plan": report_data.get("plan", []),
                "outlook": report_data.get("outlook", ""),
                "week_activities": len(recent_data),
                "ctl": latest_pmc["ctl"],
                "atl": latest_pmc["atl"],
                "tsb": latest_pmc["tsb"],
                "generated_at": user.weekly_report.generated_at.isoformat(),
            },
        }
    )


@ai_bp.route("/ai/weekly-report", methods=["GET"])
def get_weekly_report():
    """获取最近一次存储的训练报告。"""
    user, err = require_user()
    if err:
        return err

    wr = user.weekly_report
    if not wr or not wr.plan_json:
        return jsonify({"code": 200, "message": "ok", "data": None})

    return jsonify(
        {
            "code": 200,
            "message": "ok",
            "data": {
                "summary": wr.summary or "",
                "plan": json.loads(wr.plan_json) if wr.plan_json else [],
                "outlook": wr.outlook or "",
                "week_activities": wr.week_activities,
                "ctl": wr.ctl,
                "atl": wr.atl,
                "tsb": wr.tsb,
                "generated_at": wr.generated_at.isoformat() if wr.generated_at else None,
            },
        }
    )


@ai_bp.route("/ai/suggestion", methods=["POST"])
def suggestion():
    """获取个性化训练建议。"""
    user, err = require_user()
    if err:
        return err

    data = request.get_json() or {}
    question = data.get("question", "")

    try:
        latest_pmc, daily_tss, params, _ = _get_current_context(user)
    except Exception as e:
        return jsonify({"code": 500, "message": f"获取数据失败: {str(e)}", "data": None}), 500

    today = datetime.now(timezone.utc)
    recent_tss = []
    for i in range(6, -1, -1):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        recent_tss.append(daily_tss.get(date, 0))

    # 获取最近活动的最佳表现和强度分布
    recent_activities = list(
        Activity.objects(user=user, start_time__gte=(today - timedelta(days=14)).strftime("%Y-%m-%d"))
        .order_by("-start_time")
        .limit(5)
    )
    best_efforts_list = []
    intensity_counts = {}
    for a in recent_activities:
        cm = a.computed_metrics
        if not cm:
            continue
        if cm.best_efforts:
            best_efforts_list.append(
                {
                    "date": a.start_time.strftime("%m-%d"),
                    "type": a.activity_type,
                    "best_efforts": cm.best_efforts,
                }
            )
        if cm.intensity_level:
            intensity_counts[cm.intensity_level] = intensity_counts.get(cm.intensity_level, 0) + 1

    try:
        advice = generate_suggestion(latest_pmc, recent_tss, params, question, best_efforts_list, intensity_counts)
    except ValueError as e:
        return jsonify({"code": 400, "message": str(e), "data": None}), 400
    except Exception as e:
        return jsonify({"code": 500, "message": f"生成失败: {str(e)}", "data": None}), 500

    return jsonify(
        {
            "code": 200,
            "message": "ok",
            "data": {
                "suggestion": advice,
                "ctl": latest_pmc["ctl"],
                "atl": latest_pmc["atl"],
                "tsb": latest_pmc["tsb"],
            },
        }
    )
