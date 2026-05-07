from collections import defaultdict
from datetime import datetime as dt
from datetime import timedelta

from flask import Blueprint, jsonify, request

from app.models.activity import Activity
from app.services.metrics_service import calc_daily_tss, calc_pmc
from app.utils.auth import user_filter

dashboard_bp = Blueprint("dashboard", __name__)


def _filter_user(qs):
    """按当前用户过滤查询集。"""
    return user_filter(qs)


def _end_of_day(date_str):
    """将 'YYYY-MM-DD' 转为当天 23:59:59 的 datetime 对象（用于 __lte 查询）。"""
    return dt.strptime(date_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59)


@dashboard_bp.route("/pmc", methods=["GET"])
def get_pmc():
    """获取 PMC（CTL/ATL/TSB）时间序列。"""
    end_date = request.args.get("end_date", dt.now().strftime("%Y-%m-%d"))
    start_date = request.args.get(
        "start_date",
        (dt.now() - timedelta(days=60)).strftime("%Y-%m-%d"),
    )

    try:
        dt.strptime(start_date, "%Y-%m-%d")
        dt.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"code": 400, "message": "日期格式无效，应为 YYYY-MM-DD", "data": None}), 400

    activities = _filter_user(
        Activity.objects(start_time__gte=start_date, start_time__lte=_end_of_day(end_date)).exclude(
            "trackpoints", "raw_data_path"
        )
    )
    daily = calc_daily_tss(list(activities))
    pmc_data = calc_pmc(daily, start_date, end_date)

    return jsonify({"code": 200, "message": "ok", "data": pmc_data})


@dashboard_bp.route("/dashboard", methods=["GET"])
def get_dashboard():
    """获取 Dashboard 汇总数据。"""
    today = dt.now()
    start = (today - timedelta(days=90)).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")
    end_dt = _end_of_day(end)

    activities_all = _filter_user(
        Activity.objects(start_time__gte=start, start_time__lte=end_dt).exclude("trackpoints", "raw_data_path")
    )
    daily = calc_daily_tss(list(activities_all))
    # 按日期汇总活动列表（供日历浮层使用）
    calendar_activities = {}
    for a in activities_all:
        date_str = a.start_time.strftime("%Y-%m-%d")
        m = a.computed_metrics
        tss = m.manual_tss or m.tss or m.hr_tss if m else None
        calendar_activities.setdefault(date_str, []).append(
            {"id": str(a.id), "name": a.name or "", "tss": tss, "type": a.activity_type}
        )
    for acts in calendar_activities.values():
        acts.sort(key=lambda x: x.get("tss") or 0, reverse=True)
    pmc_data = calc_pmc(daily, start, end)

    latest_pmc = pmc_data[-1] if pmc_data else {"ctl": 0, "atl": 0, "tsb": 0}

    from app.blueprints.activities.routes import _serialize_activity

    recent_list = [
        _serialize_activity(a)
        for a in _filter_user(Activity.objects(start_time__lte=end_dt).exclude("trackpoints", "raw_data_path"))
        .order_by("-start_time")
        .limit(5)
    ]

    # 滚动窗口：近 7 天 / 近 30 天（比自然周/月更有训练参考价值）
    rolling_30d = (today - timedelta(days=29)).strftime("%Y-%m-%d")
    month_activities = list(
        _filter_user(
            Activity.objects(start_time__gte=rolling_30d, start_time__lte=end_dt).exclude(
                "trackpoints", "raw_data_path"
            )
        )
    )
    rolling_7d = (today - timedelta(days=6)).strftime("%Y-%m-%d")
    week_activities = [a for a in month_activities if a.start_time.strftime("%Y-%m-%d") >= rolling_7d]

    def _calc_stats(activities):
        total_tss = sum(a.computed_metrics.tss for a in activities if a.computed_metrics and a.computed_metrics.tss)
        total_duration = sum(
            a.data_summary.duration_seconds for a in activities if a.data_summary and a.data_summary.duration_seconds
        )
        total_distance = sum(
            a.data_summary.total_distance for a in activities if a.data_summary and a.data_summary.total_distance
        )
        return {
            "count": len(activities),
            "total_tss": round(total_tss, 1),
            "total_duration_minutes": round(total_duration / 60),
            "total_distance_km": round(total_distance / 1000, 1),
        }

    type_breakdown = defaultdict(int)
    for a in month_activities:
        type_breakdown[a.activity_type] += 1

    # 周趋势：最近 12 周的 TSS 和活动次数
    weekly_trend = []
    for w in range(11, -1, -1):
        week_end_date = today - timedelta(days=today.weekday() + 7 * w)
        week_start_date = week_end_date - timedelta(days=6)
        ws = week_start_date.strftime("%Y-%m-%d")
        we = week_end_date.strftime("%Y-%m-%d")
        week_tss = sum(v for k, v in daily.items() if ws <= k <= we)
        week_count = sum(1 for k, v in daily.items() if ws <= k <= we and v > 0)
        weekly_trend.append({"week": ws, "tss": round(week_tss, 1), "count": week_count})

    # 体能趋势：近期活动的 NP/EF/TSS 变化
    trend_activities = list(
        _filter_user(Activity.objects(start_time__lte=end_dt, computed_metrics__ne=None))
        .order_by("-start_time")
        .limit(30)
        .only("start_time", "computed_metrics")
    )
    fitness_trend = []
    for a in reversed(trend_activities):
        cm = a.computed_metrics
        if not cm or cm.tss is None:
            continue
        fitness_trend.append(
            {
                "date": a.start_time.strftime("%Y-%m-%d"),
                "tss": cm.tss,
                "np": cm.normalized_power,
                "if": cm.intensity_factor,
                "ef": cm.efficiency_factor,
            }
        )

    return jsonify(
        {
            "code": 200,
            "message": "ok",
            "data": {
                "ctl": latest_pmc["ctl"],
                "atl": latest_pmc["atl"],
                "tsb": latest_pmc["tsb"],
                "today_tss": daily.get(end, 0),
                "recent_activities": recent_list,
                "pmc": pmc_data[-30:],
                "calendar": daily,
                "calendar_activities": calendar_activities,
                "weekly_stats": _calc_stats(week_activities),
                "monthly_stats": _calc_stats(month_activities),
                "type_breakdown": dict(type_breakdown),
                "weekly_trend": weekly_trend,
                "fitness_trend": fitness_trend,
            },
        }
    )
