import logging
import threading
from datetime import datetime

from app.models.activity import Activity
from app.models.athlete_settings import AthleteParams

logger = logging.getLogger(__name__)


def _build_query(user, **extra_filters):
    """构建查询条件，user 为 None 时不过滤 user 字段。"""
    filters = dict(extra_filters)
    if user is not None:
        filters["user"] = user
    return filters


def get_effective_params(user, date: datetime) -> AthleteParams:
    """获取指定日期生效的运动员参数。"""
    return (
        AthleteParams.objects(
            **_build_query(user, effective_date__lte=date),
        )
        .order_by("-effective_date")
        .first()
    )


def save_params(user, params_data: dict) -> AthleteParams:
    """保存运动员参数，返回新创建的记录。"""
    effective_date = params_data["effective_date"]
    current = get_effective_params(user, effective_date)

    tracked_fields = ["ftp", "cycling_lthr", "running_lthr", "walking_lthr", "max_heart_rate", "weight"]
    has_change = False

    if current is None:
        has_change = True
    else:
        for field in tracked_fields:
            new_val = params_data.get(field)
            old_val = getattr(current, field, None)
            if new_val != old_val:
                has_change = True
                break

    if not has_change:
        return current

    params = AthleteParams(
        user=user,
        effective_date=effective_date,
        ftp=params_data.get("ftp"),
        cycling_lthr=params_data.get("cycling_lthr"),
        running_lthr=params_data.get("running_lthr"),
        walking_lthr=params_data.get("walking_lthr"),
        max_heart_rate=params_data.get("max_heart_rate"),
        weight=params_data.get("weight"),
    )
    params.save()
    return params


def get_affected_activities(user, effective_date: datetime) -> list:
    """获取受参数变更影响的活动列表。"""
    return list(
        Activity.objects(
            **_build_query(user, start_time__gte=effective_date),
        ).order_by("start_time")
    )


def recalc_activity(activity):
    """重算单个活动的指标。"""
    from app.services.metrics_service import compute_activity_metrics

    user = activity.user
    params = get_effective_params(user, activity.start_time)
    if not params:
        return

    # 重建 trackpoints 字典列表（从嵌入文档）
    if not activity.trackpoints:
        return

    trackpoints = []
    for tp in activity.trackpoints:
        d = {}
        if tp.hr is not None:
            d["heart_rate"] = tp.hr
        if tp.power is not None:
            d["power"] = tp.power
        if tp.speed is not None:
            d["speed"] = tp.speed
        if tp.cadence is not None:
            d["cadence"] = tp.cadence
        if tp.altitude is not None:
            d["altitude"] = tp.altitude
        if tp.distance is not None:
            d["distance"] = tp.distance
        # time 字段用于 duration 计算 — 使用 elapsed
        from datetime import timedelta, timezone

        d["time"] = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=tp.elapsed)
        trackpoints.append(d)

    activity_type = activity.activity_type
    hr_zones = params.get_hr_zones(activity_type)
    power_zones = params.get_power_zones() if activity_type in ("cycling", "indoor_cycling", "commute_cycling") else []

    lthr_map = {
        "cycling": params.cycling_lthr,
        "indoor_cycling": params.cycling_lthr,
        "commute_cycling": params.cycling_lthr,
        "running": params.running_lthr,
        "indoor_running": params.running_lthr,
        "walking": params.walking_lthr,
    }
    lthr = lthr_map.get(activity_type)

    activity.computed_metrics = compute_activity_metrics(
        trackpoints=trackpoints,
        activity_type=activity_type,
        hr_zones=hr_zones,
        power_zones=power_zones,
        ftp=params.ftp,
        lthr=lthr,
    )
    activity.save()


# ============================================================
# 后台重算机制
# ============================================================

_recalc_status = {}  # user_id -> {"total": N, "done": N, "running": bool}


def get_recalc_status(user_id: str) -> dict:
    """获取当前用户重算进度。"""
    return _recalc_status.get(str(user_id), {"total": 0, "done": 0, "running": False})


def mark_activities_for_recalc(user, effective_date: datetime) -> int:
    """标记需要重算的活动并启动后台重算。"""
    affected = list(
        Activity.objects(
            **_build_query(user, start_time__gte=effective_date),
        ).order_by("start_time")
    )
    count = len(affected)
    if count == 0:
        return 0

    # 初始化进度
    user_id = str(user.id)
    _recalc_status[user_id] = {"total": count, "done": 0, "running": True}

    # 测试环境中同步执行，避免数据库连接问题
    import os

    if os.environ.get("FLASK_ENV") == "testing":
        _do_recalc(user_id, affected)
    else:
        thread = threading.Thread(target=_do_recalc, args=(user_id, affected), daemon=True)
        thread.start()

    return count


def _do_recalc(user_id: str, activities: list):
    """后台线程：逐个重算活动指标。"""
    try:
        for activity in activities:
            try:
                recalc_activity(activity)
            except Exception:
                logger.exception("重算活动 %s 失败", activity.id)
            if user_id in _recalc_status:
                _recalc_status[user_id]["done"] += 1
    finally:
        if user_id in _recalc_status:
            _recalc_status[user_id]["running"] = False
