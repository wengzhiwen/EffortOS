import math
from collections import defaultdict, deque
from typing import Optional

from app.models.activity import ComputedMetrics

# 暂停间隔阈值：连续两个打点间隔超过此值视为暂停，不计入运动时长
PAUSE_GAP_SECONDS = 30

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


def calc_hr_tss(trackpoints: list[dict], lthr: int) -> Optional[float]:
    """基于心率的 TSS — 逐打点积分，跳过暂停间隔。

    TSS = Σ (dt_i / 3600) × (hr_i / LTHR)² × 100
    仅对活跃间隔（dt ≤ PAUSE_GAP_SECONDS）累加。
    """
    if not trackpoints or not lthr:
        return None
    tss = 0.0
    for i in range(1, len(trackpoints)):
        dt = (trackpoints[i]["time"] - trackpoints[i - 1]["time"]).total_seconds()
        if dt > PAUSE_GAP_SECONDS:
            continue
        hr = trackpoints[i].get("heart_rate") or trackpoints[i - 1].get("heart_rate")
        if not hr:
            continue
        tss += (dt / 3600) * (hr / lthr) ** 2 * 100
    return round(tss, 1) if tss > 0 else None


def calc_hr_efficiency_factor(avg_speed: float, avg_hr: int) -> Optional[float]:
    """计算心率效率因子 HR_EF = 平均速度 / 平均心率。

    骑行：使用 NP / avg_hr；跑步：使用 avg_speed / avg_hr。
    """
    if not avg_speed or not avg_hr:
        return None
    return round(avg_speed / avg_hr, 4)


# ============================================================
# 功率 TSS
# ============================================================


def calc_power_tss(trackpoints: list[dict], ftp: int) -> Optional[float]:
    """基于功率的 TSS — 逐打点积分，跳过暂停间隔。

    TSS = Σ (dt_i / 3600) × (power_i / FTP)² × 100
    仅对活跃间隔（dt ≤ PAUSE_GAP_SECONDS）累加。
    """
    if not trackpoints or not ftp:
        return None
    tss = 0.0
    for i in range(1, len(trackpoints)):
        dt = (trackpoints[i]["time"] - trackpoints[i - 1]["time"]).total_seconds()
        if dt > PAUSE_GAP_SECONDS:
            continue
        pw = trackpoints[i].get("power") or trackpoints[i - 1].get("power")
        if not pw:
            continue
        tss += (dt / 3600) * (pw / ftp) ** 2 * 100
    return round(tss, 1) if tss > 0 else None


# ============================================================
# 分区时间统计
# ============================================================


# ============================================================
# 强度等级判断
# ============================================================


def _rolling_average(series, window_sec=10):
    """对 (elapsed, value) 序列做时间窗口滚动平均，None 值跳过但不中断窗口。

    仅输出 raw value 非 None 的点（保持与原始时间轴对齐）。
    """
    result = []
    window = deque()  # (elapsed, value)
    for elapsed, value in series:
        while window and elapsed - window[0][0] > window_sec:
            window.popleft()
        if value is not None:
            window.append((elapsed, value))
        if value is not None and window:
            result.append((elapsed, sum(v for _, v in window) / len(window)))
    return result


def _assign_zones(smoothed, zones):
    """将平滑后的 (elapsed, value) 序列映射为 (elapsed, zone_name)。"""
    result = []
    for elapsed, value in smoothed:
        zone = None
        for z in zones:
            if z["min"] <= value < z["max"]:
                zone = z["name"]
                break
        result.append((elapsed, zone))
    return result


def _zone_times(zone_series):
    """从 zone 序列计算各区间的累计时长（秒）。"""
    zt = {}
    for i in range(1, len(zone_series)):
        dt = zone_series[i][0] - zone_series[i - 1][0]
        z = zone_series[i][1]
        if z:
            zt[z] = zt.get(z, 0) + dt
    return zt


def _continuous_zone_durations(zone_series, target_zones):
    """返回 zone_series 中连续处于 target_zones 的每段时长列表（秒）。"""
    durations = []
    block_start = None
    prev_t = None
    for t, z in zone_series:
        if z in target_zones:
            if block_start is None:
                block_start = t
        else:
            if block_start is not None:
                durations.append(prev_t - block_start)
                block_start = None
        prev_t = t
    if block_start is not None and prev_t is not None:
        durations.append(prev_t - block_start)
    return durations


def _continuous_above_durations(smoothed, threshold):
    """返回 smoothed 中连续 >= threshold 的每段时长列表（秒）。"""
    durations = []
    block_start = None
    prev_t = None
    for t, v in smoothed:
        if v is not None and v >= threshold:
            if block_start is None:
                block_start = t
        else:
            if block_start is not None:
                durations.append(prev_t - block_start)
                block_start = None
        prev_t = t
    if block_start is not None and prev_t is not None:
        durations.append(prev_t - block_start)
    return durations


def _fmt_min(seconds):
    """将秒格式化为可读的时间字符串。"""
    if seconds < 60:
        return f"{int(seconds)}秒"
    m = seconds / 60
    if m == int(m):
        return f"{int(m)}分钟"
    return f"{m:.1f}分钟"


def _classify_smoothed(smoothed, zones, high_threshold):
    """对已平滑的序列按运动科学标准判断强度等级。

    返回 (level, reason_dict) 或 (None, reason_dict)。
    reason_dict 包含 method/strict/zone_times/matched 等字段。
    """
    total_duration = smoothed[-1][0] - smoothed[0][0] if len(smoothed) >= 2 else 0
    zone_series = _assign_zones(smoothed, zones) if smoothed else []
    zt = _zone_times(zone_series) if zone_series else {}

    def _reason(strict, matched):
        return {"strict": strict, "zone_times": {k: round(v, 0) for k, v in zt.items()}, "matched": matched}

    if len(smoothed) < 2:
        return None, _reason(False, "数据不足")

    high_zones = {"Z5", "Z6", "Z7"}
    zone_cn = {
        "Z1": "Z1 恢复",
        "Z2": "Z2 有氧",
        "Z3": "Z3 节奏",
        "Z4": "Z4 阈值",
        "Z5": "Z5 VO2max",
        "Z6": "Z6 无氧",
        "Z7": "Z7 神经肌肉",
    }

    # VO2max: Z5+ ≥ 15 min，≥ 3 段连续 3+ min
    vo2_time = sum(zt.get(z, 0) for z in high_zones)
    if vo2_time >= 900:
        blocks = _continuous_zone_durations(zone_series, high_zones)
        long_blocks = [b for b in blocks if b >= 180]
        if len(long_blocks) >= 3:
            return "vo2max", _reason(
                True,
                f"Z5+ 累计 {_fmt_min(vo2_time)}（≥15分钟），"
                f"连续3分钟以上间歇 {len(long_blocks)} 组（≥3组），最长 {_fmt_min(max(long_blocks))}",
            )

    # Threshold: Z4 ≥ 25 min，≥ 1 段连续 8+ min
    z4_time = zt.get("Z4", 0)
    if z4_time >= 1500:
        blocks = _continuous_zone_durations(zone_series, {"Z4"})
        longest = max(blocks) if blocks else 0
        if longest >= 480:
            return "threshold", _reason(
                True,
                f"Z4 累计 {_fmt_min(z4_time)}（≥25分钟），最长连续 {_fmt_min(longest)}（≥8分钟）",
            )

    # Tempo: Z3 ≥ 30 min，≥ 1 段连续 15+ min
    z3_time = zt.get("Z3", 0)
    if z3_time >= 1800:
        blocks = _continuous_zone_durations(zone_series, {"Z3"})
        longest = max(blocks) if blocks else 0
        if longest >= 900:
            return "tempo", _reason(
                True,
                f"Z3 累计 {_fmt_min(z3_time)}（≥30分钟），最长连续 {_fmt_min(longest)}（≥15分钟）",
            )

    # Endurance: 总时长 ≥ 45 min，Z2 ≥ 30 min，Z3+ < 10%
    above_z2_zones = {"Z3", "Z4", "Z5", "Z6", "Z7"}
    above_z2 = sum(zt.get(z, 0) for z in above_z2_zones)
    z2_time = zt.get("Z2", 0)
    if total_duration >= 2700 and z2_time >= 1800 and above_z2 < total_duration * 0.10:
        return "endurance", _reason(
            True,
            f"总时长 {_fmt_min(total_duration)}（≥45分钟），"
            f"Z2 {_fmt_min(z2_time)}（≥30分钟），Z3以上仅占 {above_z2 / total_duration * 100:.0f}%",
        )

    # Recovery: Z1 ≥ 70% 总时长，且无连续 3+ min 超过 high_threshold
    z1_time = zt.get("Z1", 0)
    if total_duration > 0 and z1_time >= total_duration * 0.70:
        blocks = _continuous_above_durations(smoothed, high_threshold)
        if not any(b >= 180 for b in blocks):
            return "recovery", _reason(
                True,
                f"Z1 占总时长 {z1_time / total_duration * 100:.0f}%（≥70%），无连续3分钟以上高强度段",
            )

    # Fallback: 按非 Z1 区域的主导区间粗略归类
    if total_duration >= 600:
        non_z1 = {z: t for z, t in zt.items() if z not in (None, "Z1") and t > 0}
        if non_z1:
            dominant = max(non_z1, key=non_z1.get)
            zone_level = {
                "Z5": "vo2max",
                "Z6": "vo2max",
                "Z7": "vo2max",
                "Z4": "threshold",
                "Z3": "tempo",
                "Z2": "endurance",
            }
            if dominant in zone_level and non_z1[dominant] >= 300:
                label = zone_cn.get(dominant, dominant)
                return (
                    zone_level[dominant],
                    _reason(False, f"按主导区间归类：{label} 累计 {_fmt_min(non_z1[dominant])}（占比最高）"),
                )
        if zt.get("Z1", 0) >= total_duration * 0.50:
            return "recovery", _reason(False, f"Z1 占总时长 {zt['Z1'] / total_duration * 100:.0f}%（≥50%）")

    return None, _reason(False, "未满足任何分类标准")


_LEVEL_ORDER = {"recovery": 0, "endurance": 1, "tempo": 2, "threshold": 3, "vo2max": 4}

# Coggan 经典 IF 区间 → 最低强度等级
_IF_FLOOR = [
    (0.95, "threshold"),
    (0.85, "tempo"),
    (0.75, "endurance"),
]


def _calc_intensity_level(
    trackpoints: list,
    activity_type: str,
    power_zones: list[dict],
    hr_zones: list[dict],
    ftp: Optional[int] = None,
    lthr: Optional[int] = None,
    intensity_factor: Optional[float] = None,
    hr_intensity_factor: Optional[float] = None,
):
    """基于 10 秒平滑功率/心率的区间停留时长判断强度等级。

    优先功率（骑行），无可靠功率时心率兜底。
    当区间分析结果低于 IF/HRIF 所暗示的强度时，以 IF 为下限上调。
    返回 (level, reason_dict)。
    """
    if not trackpoints or len(trackpoints) < 2:
        return None, {}

    start_time = trackpoints[0]["time"]
    is_cycling = activity_type in ("cycling", "indoor_cycling", "commute_cycling")

    # 构建 (elapsed, value) 序列
    power_series = [((tp["time"] - start_time).total_seconds(), tp.get("power")) for tp in trackpoints]
    hr_series = [((tp["time"] - start_time).total_seconds(), tp.get("heart_rate")) for tp in trackpoints]

    result, reason = None, {}

    # 功率路径（骑行 + 有功率区 + 有 FTP）
    if is_cycling and power_zones and ftp:
        smoothed = _rolling_average(power_series, 10)
        # 至少 10 min 有效功率数据
        if len(smoothed) >= 600:
            result, reason = _classify_smoothed(smoothed, power_zones, ftp * 0.90)
            if result is not None:
                reason["method"] = "power"

    # 心率路径（功率路径未命中时兜底）
    if result is None and hr_zones and lthr:
        smoothed = _rolling_average(hr_series, 10)
        if len(smoothed) >= 600:
            result, reason = _classify_smoothed(smoothed, hr_zones, lthr * 0.94)
            reason["method"] = "hr"

    # IF 下限校正：高强度间歇等场景下区间分析可能低估，用 IF 兜底
    if result is not None:
        if_val = intensity_factor if reason.get("method") == "power" else hr_intensity_factor
        if if_val is not None:
            for threshold, floor_level in _IF_FLOOR:
                if if_val >= threshold:
                    if _LEVEL_ORDER.get(floor_level, 0) > _LEVEL_ORDER.get(result, 0):
                        prev = result
                        result = floor_level
                        reason["matched"] += f"；IF={if_val:.3f} ≥ {threshold}，由 {prev} 上调至 {floor_level}"
                    break

    return result, reason


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
# Best Efforts（最佳表现）
# ============================================================

BEST_EFFORT_WINDOWS = [5, 15, 30, 60, 120, 300, 600, 1200, 3600]  # 秒


def calc_best_efforts(trackpoints: list[dict]) -> dict:
    """计算不同时间窗口的最佳功率和最佳心率。

    使用滑动窗口算法：对每个时间窗口，找出窗口内功率/心率的最高时间加权平均值。

    返回: {
        "power": {5: 450, 15: 380, 60: 320, ...},
        "heart_rate": {5: 178, 15: 176, 60: 172, ...}
    }
    """
    if not trackpoints or len(trackpoints) < 2:
        return {}

    n = len(trackpoints)
    # 计算相邻 trackpoint 的时间间隔
    intervals = []
    for i in range(1, n):
        dt = (trackpoints[i]["time"] - trackpoints[i - 1]["time"]).total_seconds()
        intervals.append(max(dt, 0.5))

    # 总时长
    total_time = sum(intervals)

    # 预提取有效值序列
    power_seq = [tp.get("power") for tp in trackpoints]
    hr_seq = [tp.get("heart_rate") for tp in trackpoints]

    result = {}

    for window_sec in BEST_EFFORT_WINDOWS:
        if window_sec > total_time * 1.1:  # 数据总时长不够（留 10% 余量）
            continue

        best_power = None
        best_hr = None

        # 滑动窗口：对每个起点，累积时间直到达到窗口
        i = 0
        while i < n:
            cum_time = 0.0
            cum_power_time = 0.0  # 功率 × 时间的加权累积
            cum_hr_time = 0.0
            cum_weight_p = 0.0  # 权重累积（时间）
            cum_weight_h = 0.0
            j = i

            while j < n:
                seg = intervals[j - 1] if j > i else 0.0
                cum_time += seg
                if cum_time > window_sec and j > i:
                    break

                if power_seq[j] is not None:
                    cum_power_time += power_seq[j] * max(seg, 1.0)
                    cum_weight_p += max(seg, 1.0)
                if hr_seq[j] is not None:
                    cum_hr_time += hr_seq[j] * max(seg, 1.0)
                    cum_weight_h += max(seg, 1.0)
                j += 1

            if cum_time >= window_sec * 0.9:  # 允许 10% 误差
                if cum_weight_p > 0:
                    avg_p = cum_power_time / cum_weight_p
                    if best_power is None or avg_p > best_power:
                        best_power = round(avg_p)
                if cum_weight_h > 0:
                    avg_h = cum_hr_time / cum_weight_h
                    if best_hr is None or avg_h > best_hr:
                        best_hr = round(avg_h)

            i += 1

        if best_power is not None or best_hr is not None:
            if "power" not in result and best_power is not None:
                result["power"] = {}
            if "heart_rate" not in result and best_hr is not None:
                result["heart_rate"] = {}
            if best_power is not None:
                result["power"][str(window_sec)] = best_power
            if best_hr is not None:
                result["heart_rate"][str(window_sec)] = best_hr

    return result


# ============================================================
# 跑步配速最佳表现
# ============================================================

PACE_BEST_EFFORT_DISTANCES = [400, 1000, 3000, 5000, 10000, 15000, 21100, 42200]  # 米


def calc_pace_best_efforts(trackpoints: list[dict]) -> dict:
    """基于距离滑动窗口计算各标准距离的最佳配速（秒/公里）。

    对每个目标距离，在 trackpoints 中找到恰好覆盖该距离的最短时间窗口，
    计算平均配速。使用双指针滑动窗口算法。

    返回: {"400": pace_sec_per_km, "1000": pace_sec_per_km, ...}
    """
    if not trackpoints or len(trackpoints) < 2:
        return {}

    # 过滤有效打点（有 distance 和 time）
    valid = []
    for tp in trackpoints:
        d = tp.get("distance")
        if d is not None and d >= 0:
            valid.append((tp["time"], d))

    if len(valid) < 2:
        return {}

    total_dist = valid[-1][1] - valid[0][1]
    result = {}

    for target_dist in PACE_BEST_EFFORT_DISTANCES:
        if total_dist < target_dist * 0.9:
            continue

        best_pace = None  # 秒/公里
        j = 0  # 尾指针

        for i in range(len(valid)):
            # 前进尾指针直到窗口不超过目标距离
            while j < i and (valid[i][1] - valid[j][1]) > target_dist * 1.02:
                j += 1

            # 从尾指针向头指针搜索最接近 target_dist 的窗口
            for k in range(j, i + 1):
                dist_covered = valid[i][1] - valid[k][1]
                if dist_covered < target_dist * 0.95:
                    break
                time_covered = (valid[i][0] - valid[k][0]).total_seconds()
                if time_covered <= 0:
                    continue
                pace_sec_per_km = (time_covered / dist_covered) * 1000
                if best_pace is None or pace_sec_per_km < best_pace:
                    best_pace = pace_sec_per_km

        if best_pace is not None:
            result[str(target_dist)] = round(best_pace, 1)

    return result


def calc_grade_adjusted_pace(speed_mps: float, grade_pct: float) -> Optional[float]:
    """计算坡度调整配速(GAP)对应速度。

    GAP_speed = speed / (1 + grade_pct * 0.04)
    上坡 grade_pct > 0 → GAP_speed < speed（等效更慢）
    下坡 grade_pct < 0 → GAP_speed > speed（等效更快）

    返回调整后的速度 (m/s)，可用于计算等效配速。
    """
    if not speed_mps or speed_mps <= 0:
        return None
    factor = 1 + grade_pct * 0.04
    if factor <= 0:
        return None
    return speed_mps / factor


# ============================================================


def _calc_active_duration(trackpoints, gap_threshold=PAUSE_GAP_SECONDS):
    """计算活跃运动时长（排除暂停间隔）。

    相邻打点间隔 > gap_threshold 视为暂停，不计入运动时长。
    返回 (active_seconds, gap_seconds)。
    """
    if not trackpoints or len(trackpoints) < 2:
        return 0.0, 0.0
    active = 0.0
    gap = 0.0
    for i in range(1, len(trackpoints)):
        dt = (trackpoints[i]["time"] - trackpoints[i - 1]["time"]).total_seconds()
        if dt > gap_threshold:
            gap += dt
        else:
            active += dt
    return active, gap


def _split_segments(trackpoints, gap_threshold=PAUSE_GAP_SECONDS):
    """将 trackpoints 按暂停间隔拆分为活跃段列表。

    返回 list[list[dict]]，每个子列表是一段连续活跃数据。
    """
    if not trackpoints:
        return []
    segments = [[trackpoints[0]]]
    for i in range(1, len(trackpoints)):
        dt = (trackpoints[i]["time"] - trackpoints[i - 1]["time"]).total_seconds()
        if dt > gap_threshold:
            segments.append([])
        segments[-1].append(trackpoints[i])
    return [s for s in segments if len(s) >= 2]


def _calc_work_kj_time_aware(trackpoints):
    """使用实际时间间隔计算总做功（kJ）。"""
    work_j = 0.0
    for i in range(1, len(trackpoints)):
        dt = (trackpoints[i]["time"] - trackpoints[i - 1]["time"]).total_seconds()
        if dt > PAUSE_GAP_SECONDS:
            continue
        p0 = trackpoints[i - 1].get("power")
        p1 = trackpoints[i].get("power")
        if p0 is not None and p1 is not None:
            work_j += (p0 + p1) / 2 * dt
        elif p0 is not None:
            work_j += p0 * dt
        elif p1 is not None:
            work_j += p1 * dt
    return round(work_j / 1000, 1) if work_j > 0 else None


def _calc_zone_times_time_aware(trackpoints, field, zones):
    """使用实际时间间隔计算分区时间分布。"""
    result = {z["name"]: 0.0 for z in zones}
    for i in range(1, len(trackpoints)):
        dt = (trackpoints[i]["time"] - trackpoints[i - 1]["time"]).total_seconds()
        if dt > PAUSE_GAP_SECONDS:
            continue
        val = trackpoints[i].get(field)
        if val is None:
            continue
        for zone in zones:
            if zone["min"] <= val < zone["max"]:
                result[zone["name"]] += dt
                break
    return {k: round(v, 1) for k, v in result.items()}


def _calc_segmented_np(trackpoints, power_field="power"):
    """按活跃段分别计算 NP，合并时按段时长加权。

    避免 30s 滚动窗口跨越暂停间隔。
    """
    segments = _split_segments(trackpoints)
    if not segments:
        return None

    all_rolling = []
    for seg in segments:
        pvs = [tp.get(power_field) for tp in seg if tp.get(power_field) is not None]
        if len(pvs) < 30:
            # 不足 30s，直接加入原始值
            all_rolling.extend(pvs)
            continue
        for i in range(len(pvs) - 29):
            all_rolling.append(sum(pvs[i : i + 30]) / 30)

    if not all_rolling:
        return None
    fourth_power_sum = sum(v**4 for v in all_rolling)
    return round((fourth_power_sum / len(all_rolling)) ** 0.25, 1)


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

    active_duration, _gap_duration = _calc_active_duration(trackpoints)
    avg_hr = sum(hr_values) // len(hr_values) if hr_values else None

    has_power = len(power_values) > 0
    has_hr = len(hr_values) > 0
    is_cycling = activity_type in ("cycling", "indoor_cycling", "commute_cycling")
    is_running = activity_type in ("running", "indoor_running", "walking")
    is_commute = activity_type == "commute_cycling"

    # 判断功率数据质量：覆盖率低于 50% 视为不可靠
    power_coverage = len(power_values) / total_points if total_points > 0 else 0
    power_reliable = has_power and power_coverage >= 0.5

    # 功率衍生指标（仅骑行且有可靠功率数据时）
    if power_reliable and is_cycling:
        metrics.normalized_power = _calc_segmented_np(trackpoints, "power")
        avg_power = sum(power_values) / len(power_values)
        metrics.work_kj = _calc_work_kj_time_aware(trackpoints)

        if metrics.normalized_power:
            metrics.variability_index = calc_variability_index(metrics.normalized_power, avg_power)

            if avg_hr:
                metrics.efficiency_factor = calc_power_efficiency_factor(metrics.normalized_power, avg_hr)

        if ftp:
            metrics.intensity_factor = calc_intensity_factor(metrics.normalized_power or avg_power, ftp)
            metrics.tss = calc_power_tss(trackpoints, ftp)
            metrics.tss_method = "power"

    # 心率衍生指标
    if has_hr and lthr:
        metrics.hr_intensity_factor = calc_hr_intensity_factor(avg_hr, lthr)
        metrics.hr_tss = calc_hr_tss(trackpoints, lthr)
        # 通勤骑行且无功率 TSS 时，TSS = hrTSS × 0.75
        if is_commute and metrics.tss is None and metrics.hr_tss is not None:
            metrics.tss = round(metrics.hr_tss * 0.75, 1)
            metrics.tss_method = "hr_commute"

    # 跑步效率因子: avg_speed / avg_hr（骑行 EF = NP/avgHR 在功率块中已计算）
    if is_running and has_hr:
        speed_values = [tp.get("speed") for tp in trackpoints if tp.get("speed") is not None]
        if speed_values:
            avg_speed = sum(speed_values) / len(speed_values)
            metrics.efficiency_factor = calc_hr_efficiency_factor(avg_speed, avg_hr)

    # 分区时间统计（使用实际时间间隔）
    if has_hr and hr_zones:
        metrics.hr_zones_time = _calc_zone_times_time_aware(trackpoints, "heart_rate", hr_zones)

    if has_power and power_zones:
        metrics.power_zones_time = _calc_zone_times_time_aware(trackpoints, "power", power_zones)

    # Best Efforts：不同时长的峰值功率和峰值心率
    best_efforts = calc_best_efforts(trackpoints)
    if best_efforts:
        metrics.best_efforts = best_efforts

    # 跑步配速最佳表现：标准距离的最佳配速
    if is_running:
        pace_efforts = calc_pace_best_efforts(trackpoints)
        if pace_efforts:
            metrics.pace_best_efforts = pace_efforts

    # 强度评级：基于有效训练时间的区间占比
    metrics.intensity_level, metrics.intensity_reason = _calc_intensity_level(
        trackpoints=trackpoints,
        activity_type=activity_type,
        power_zones=power_zones if power_reliable and is_cycling else [],
        hr_zones=hr_zones,
        ftp=ftp,
        lthr=lthr,
        intensity_factor=metrics.intensity_factor,
        hr_intensity_factor=metrics.hr_intensity_factor,
    )

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
        m = activity.computed_metrics
        if not m:
            continue
        # 优先级：手动 > 功率 TSS > hrTSS
        tss = m.manual_tss or m.tss or m.hr_tss
        if tss:
            date_str = activity.start_time.strftime("%Y-%m-%d")
            daily[date_str] += tss
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


# ============================================================
# 分段分析（Lap Splits）
# ============================================================


def calc_lap_splits(
    trackpoints: list[dict],
    mode: str = "distance",
    interval: float = 1000,
) -> list[dict]:
    """将活动按距离或时间分段，每段独立统计。

    参数:
        trackpoints: 解析后的时间序列数据（需有 time, distance 字段）
        mode: "distance" 按距离分段（interval 单位米），"time" 按时间分段（interval 单位秒）
        interval: 分段间隔

    返回: [
        {
            "lap": 1,
            "start_elapsed": 秒,
            "end_elapsed": 秒,
            "duration_seconds": 秒,
            "distance_meters": 米,
            "avg_speed_kmh": km/h,
            "avg_hr": bpm,
            "max_hr": bpm,
            "avg_power": W,
            "max_power": W,
            "avg_cadence": rpm,
        },
        ...
    ]
    """
    if not trackpoints or len(trackpoints) < 2:
        return []

    n = len(trackpoints)
    laps = []
    lap_idx = 1

    if mode == "distance":
        next_boundary = interval
        lap_start = 0

        for i in range(1, n):
            dist = trackpoints[i].get("distance")
            if dist is not None and dist >= next_boundary:
                laps.append(_extract_lap_stats(trackpoints, lap_start, i, lap_idx))
                lap_idx += 1
                lap_start = i
                next_boundary += interval

        # 最后一段
        if lap_start < n - 1:
            lap = _extract_lap_stats(trackpoints, lap_start, n - 1, lap_idx)
            if lap["duration_seconds"] > 0:
                laps.append(lap)

    elif mode == "time":
        next_boundary = interval
        lap_start = 0
        start_time = trackpoints[0]["time"]

        for i in range(1, n):
            elapsed = (trackpoints[i]["time"] - start_time).total_seconds()
            if elapsed >= next_boundary:
                laps.append(_extract_lap_stats(trackpoints, lap_start, i, lap_idx))
                lap_idx += 1
                lap_start = i
                next_boundary += interval

        if lap_start < n - 1:
            lap = _extract_lap_stats(trackpoints, lap_start, n - 1, lap_idx)
            if lap["duration_seconds"] > 0:
                laps.append(lap)

    return laps


def _extract_lap_stats(trackpoints: list[dict], start: int, end: int, lap_idx: int) -> dict:
    """提取一个分段内的统计数据。"""
    t_start = trackpoints[start]["time"]
    t_end = trackpoints[end]["time"]
    duration = (t_end - t_start).total_seconds()

    dist_start = trackpoints[start].get("distance") or 0
    dist_end = trackpoints[end].get("distance") or 0
    distance = dist_end - dist_start

    hrs = [trackpoints[i].get("heart_rate") for i in range(start, end + 1)]
    hrs = [v for v in hrs if v is not None]

    powers = [trackpoints[i].get("power") for i in range(start, end + 1)]
    powers = [v for v in powers if v is not None]

    cadences = [trackpoints[i].get("cadence") for i in range(start, end + 1)]
    cadences = [v for v in cadences if v is not None]

    avg_speed = (distance / duration * 3.6) if duration > 0 and distance > 0 else None

    return {
        "lap": lap_idx,
        "start_elapsed": (t_start - trackpoints[0]["time"]).total_seconds(),
        "end_elapsed": (t_end - trackpoints[0]["time"]).total_seconds(),
        "duration_seconds": round(duration, 1),
        "distance_meters": round(distance, 1),
        "avg_speed_kmh": round(avg_speed, 1) if avg_speed else None,
        "avg_hr": round(sum(hrs) / len(hrs)) if hrs else None,
        "max_hr": max(hrs) if hrs else None,
        "avg_power": round(sum(powers) / len(powers)) if powers else None,
        "max_power": max(powers) if powers else None,
        "avg_cadence": round(sum(cadences) / len(cadences)) if cadences else None,
    }
