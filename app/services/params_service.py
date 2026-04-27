from datetime import datetime

from app.models.activity import Activity
from app.models.athlete_settings import AthleteParams


def _build_query(user, **extra_filters):
    """构建查询条件，user 为 None 时不过滤 user 字段。"""
    filters = dict(extra_filters)
    if user is not None:
        filters["user"] = user
    return filters


def get_effective_params(user, date: datetime) -> AthleteParams:
    """获取指定日期生效的运动员参数。

    返回 effective_date <= date 的最新一条记录。
    """
    return (
        AthleteParams.objects(
            **_build_query(user, effective_date__lte=date),
        )
        .order_by("-effective_date")
        .first()
    )


def save_params(user, params_data: dict) -> AthleteParams:
    """保存运动员参数，返回新创建的记录。

    检测参数是否有实质性变更，如无变更则不创建新记录。
    """
    effective_date = params_data["effective_date"]

    # 查看当前生效的参数
    current = get_effective_params(user, effective_date)

    # 检查是否有实质性变更
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
    """获取受参数变更影响的活动列表。

    返回 start_time >= effective_date 的所有活动。
    """
    return list(
        Activity.objects(
            **_build_query(user, start_time__gte=effective_date),
        ).order_by("start_time")
    )


def mark_activities_for_recalc(user, effective_date: datetime) -> int:
    """标记需要重算的活动。

    将 computed_metrics 清空，表示需要重新计算。
    返回受影响的活动数量。
    """
    affected = Activity.objects(
        **_build_query(user, start_time__gte=effective_date),
    )
    count = affected.count()
    affected.update(unset__computed_metrics=1)
    return count
