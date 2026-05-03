import math
from collections import defaultdict
from typing import Optional

from app.models.activity import ComputedMetrics

# ============================================================
# 功率衍生指标
# ============================================================


def calc_normalized_power(power_values: list[int]) -> Optional[float]:
    """计算标准化功率（Normalized Power）。

    步骤：30 秒滚动平均 → 取 4 次方 → 求均值 → 开 4 次方根。
    power_values 应为逐秒（或逐数据点）的功率值列表。
    """
    if not power_values:
        return None

    # 30 秒滚动平均（假设数据点间隔 1 秒）
    window = 30
    if len(power_values) < window:
        # 数据不足 30 秒，直接用全部数据
        rolling = power_values
    else:
        rolling = []
        for i in range(len(power_values) - window + 1):
            avg = sum(power_values[i : i + window]) / window
            rolling.append(avg)

    if not rolling:
        return None

    # 取 4 次方 → 求均值 → 开 4 次方根
    fourth_power_sum = sum(v**4 for v in rolling)
    np_val = (fourth_power_sum / len(rolling)) ** 0.25
    return round(np_val, 1)


def calc_intensity_factor(np_val: float, ftp: int) -> Optional[float]:
    """计算强度因子 IF = NP / FTP。"""
    if not np_val or not ftp:
        return None
    return round(np_val / ftp, 3)


def calc_variability_index(np_val: float, avg_power: float) -> Optional[float]:
    """计算变异性指数 VI = NP / 平均功率。"""
    if not np_val or not avg_power:
        return None
    return round(np_val / avg_power, 3)


def calc_power_efficiency_factor(np_val: float, avg_hr: int) -> Optional[float]:
    """计算功率效率因子 EF = NP / 平均心率。"""
    if not np_val or not avg_hr:
        return None
    return round(np_val / avg_hr, 3)


def calc_work_kj(power_values: list[int], interval_seconds: float = 1.0) -> Optional[float]:
    """计算总做功（kJ）= sum(power * dt) / 1000。"""
    if not power_values:
        return None
    work_j = sum(p * interval_seconds for p in power_values)
    return round(work_j / 1000, 1)


# ============================================================
# 心率衍生指标
# ============================================================


def calc_hr_intensity_factor(avg_hr: int, lthr: int) -> Optional[float]:
    """计算心率强度因子 HR_IF = 平均心率 / LTHR。"""
    if not avg_hr or not lthr:
        return None
    return round(avg_hr / lthr, 3)


def calc_hr_tss(duration_seconds: int, avg_hr: int, lthr: int) -> Optional[float]:
    """计算基于心率的 TSS = duration_hours * HR_IF^2 * 100。"""
    if not duration_seconds or not avg_hr or not lthr:
        return None
    hr_if = avg_hr / lthr
    duration_hours = duration_seconds / 3600
    return round(duration_hours * hr_if**2 * 100, 1)


def calc_hr_efficiency_factor(avg_speed: float, avg_hr: int) -> Optional[float]:
    """计算心率效率因子 HR_EF = 平均速度 / 平均心率。"""
    if not avg_speed or not avg_hr:
        return None
    return round(avg_speed / avg_hr, 4)


# ============================================================
# 功率 TSS
# ============================================================


def calc_power_tss(duration_seconds: int, np_val: float, ftp: int) -> Optional[float]:
    """计算基于功率的 TSS = duration_hours * IF^2 * 100。"""
    if not duration_seconds or not np_val or not ftp:
        return None
    if_val = np_val / ftp
    duration_hours = duration_seconds / 3600
    return round(duration_hours * if_val**2 * 100, 1)


# ============================================================
# 分区时间统计
# ============================================================


def calc_zone_times(
    values: list[Optional[float]],
    zones: list[dict],
    interval_seconds: float = 1.0,
) -> dict[str, float]:
    """计算分区时间分布。

    values: 时间序列值列表
    zones: [{"name": "Z1", "min": 0, "max": X}, ...]
    interval_seconds: 数据点间隔（秒）

    返回 {"Z1": 秒数, "Z2": 秒数, ...}
    """
    result = {z["name"]: 0.0 for z in zones}

    for val in values:
        if val is None:
            continue
        for zone in zones:
            if zone["min"] <= val < zone["max"]:
                result[zone["name"]] += interval_seconds
                break

    return {k: round(v, 1) for k, v in result.items()}


# ============================================================
# 统一计算入口
# ============================================================


def compute_activity_metrics(
    trackpoints: list[dict],
    activity_type: str,
    hr_zones: list[dict],
    power_zones: list[dict],
    ftp: Optional[int] = None,
    lthr: Optional[int] = None,
) -> ComputedMetrics:
    """根据运动类型和数据，计算所有可计算的指标。

    参数:
        trackpoints: 解析后的时间序列数据
        activity_type: 运动类型
        hr_zones: 心率分区定义（从 AthleteParams.get_hr_zones 获取）
        power_zones: 功率分区定义（从 AthleteParams.get_power_zones 获取）
        ftp: 功能阈值功率（骑行时使用）
        lthr: 阈值心率（对应运动类型的 LTHR）

    返回: ComputedMetrics 嵌入文档
    """
    metrics = ComputedMetrics()

    if not trackpoints:
        return metrics

    total_points = len(trackpoints)
    power_values = [tp["power"] for tp in trackpoints if tp.get("power") is not None]
    hr_values = [tp["heart_rate"] for tp in trackpoints if tp.get("heart_rate") is not None]

    duration = (trackpoints[-1]["time"] - trackpoints[0]["time"]).total_seconds()
    avg_hr = sum(hr_values) // len(hr_values) if hr_values else None

    has_power = len(power_values) > 0
    has_hr = len(hr_values) > 0
    is_cycling = activity_type in ("cycling", "indoor_cycling")

    # 判断功率数据质量：覆盖率低于 50% 视为不可靠
    power_coverage = len(power_values) / total_points if total_points > 0 else 0
    power_reliable = has_power and power_coverage >= 0.5

    # 功率衍生指标（仅骑行且有可靠功率数据时）
    if power_reliable and is_cycling:
        metrics.normalized_power = calc_normalized_power(power_values)
        avg_power = sum(power_values) / len(power_values)
        metrics.work_kj = calc_work_kj(power_values)

        if metrics.normalized_power:
            metrics.variability_index = calc_variability_index(metrics.normalized_power, avg_power)

            if avg_hr:
                metrics.efficiency_factor = calc_power_efficiency_factor(metrics.normalized_power, avg_hr)

        if ftp and metrics.normalized_power:
            metrics.intensity_factor = calc_intensity_factor(metrics.normalized_power, ftp)
            metrics.tss = calc_power_tss(duration, metrics.normalized_power, ftp)
            metrics.tss_method = "power"

    # 心率衍生指标
    if has_hr and lthr:
        metrics.hr_intensity_factor = calc_hr_intensity_factor(avg_hr, lthr)
        metrics.hr_tss = calc_hr_tss(duration, avg_hr, lthr)

        # TSS 策略：功率未算出 或 功率数据不可靠 → 心率兜底
        if metrics.tss is None and metrics.hr_tss is not None:
            metrics.tss = metrics.hr_tss
            metrics.tss_method = "hr"

    # 分区时间统计
    if has_hr and hr_zones:
        metrics.hr_zones_time = calc_zone_times(hr_values, hr_zones)

    if has_power and power_zones:
        metrics.power_zones_time = calc_zone_times(power_values, power_zones)

    # 强度评级：基于 IF（功率优先，心率兜底）
    if_val = metrics.intensity_factor or metrics.hr_intensity_factor
    if if_val:
        if if_val < 0.65:
            metrics.intensity_level = "recovery"
        elif if_val < 0.80:
            metrics.intensity_level = "endurance"
        elif if_val < 0.90:
            metrics.intensity_level = "tempo"
        elif if_val < 1.05:
            metrics.intensity_level = "threshold"
        else:
            metrics.intensity_level = "vo2max"

    return metrics


# ============================================================
# PMC 计算（CTL/ATL/TSB）
# ============================================================

ALPHA_CTL = 1 - math.exp(-1 / 42)  # ≈ 0.02353
ALPHA_ATL = 1 - math.exp(-1 / 7)  # ≈ 0.13307


def calc_daily_tss(activities: list) -> dict[str, float]:
    """将活动列表按日期汇总为每日 TSS。

    返回 {"2026-04-27": 85.5, "2026-04-28": 120.0, ...}
    """
    daily = defaultdict(float)
    for activity in activities:
        if activity.computed_metrics and activity.computed_metrics.tss:
            date_str = activity.start_time.strftime("%Y-%m-%d")
            daily[date_str] += activity.computed_metrics.tss
    return dict(daily)


def calc_pmc(daily_tss: dict[str, float], start_date: str, end_date: str) -> list[dict]:
    """计算 PMC（CTL/ATL/TSB）时间序列。

    参数:
        daily_tss: {"2026-04-27": 85.5, ...}
        start_date: 起始日期 "YYYY-MM-DD"
        end_date: 结束日期 "YYYY-MM-DD"

    返回: [{"date": "2026-04-27", "tss": 85.5, "ctl": ..., "atl": ..., "tsb": ...}, ...]
    """
    from datetime import datetime, timedelta

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    ctl = 0.0
    atl = 0.0
    result = []

    current = start
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        day_tss = daily_tss.get(date_str, 0.0)

        ctl = ctl + (day_tss - ctl) * ALPHA_CTL
        atl = atl + (day_tss - atl) * ALPHA_ATL
        tsb = ctl - atl

        result.append(
            {
                "date": date_str,
                "tss": day_tss,
                "ctl": round(ctl, 1),
                "atl": round(atl, 1),
                "tsb": round(tsb, 1),
            }
        )

        current += timedelta(days=1)

    return result
