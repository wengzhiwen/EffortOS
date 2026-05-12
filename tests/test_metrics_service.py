from datetime import datetime, timedelta, timezone

from app.services.metrics_service import (
    calc_grade_adjusted_pace,
    calc_hr_efficiency_factor,
    calc_hr_intensity_factor,
    calc_hr_tss,
    calc_intensity_factor,
    calc_normalized_power,
    calc_pace_best_efforts,
    calc_pmc,
    calc_power_efficiency_factor,
    calc_power_tss,
    calc_variability_index,
    calc_work_kj,
    calc_zone_times,
    compute_activity_metrics,
)

# ============================================================
# 功率衍生指标测试
# ============================================================


def test_normalized_power_steady():
    # 稳态 200W，NP 应接近 200
    powers = [200] * 3600
    np_val = calc_normalized_power(powers)
    assert abs(np_val - 200.0) < 1.0


def test_normalized_power_variable():
    # 交替高功率和低功率，NP 应高于平均功率
    powers = [100] * 1800 + [300] * 1800
    np_val = calc_normalized_power(powers)
    avg = sum(powers) / len(powers)
    assert np_val > avg  # NP 受高值影响更大


def test_normalized_power_short():
    # 少于 30 个点
    powers = [150, 160, 170, 180, 190]
    np_val = calc_normalized_power(powers)
    assert np_val is not None
    assert np_val > 0


def test_normalized_power_empty():
    assert calc_normalized_power([]) is None


def test_intensity_factor():
    assert calc_intensity_factor(250.0, 250) == 1.0
    assert calc_intensity_factor(200.0, 250) == 0.8
    assert calc_intensity_factor(0, 250) is None
    assert calc_intensity_factor(200.0, 0) is None


def test_variability_index():
    assert calc_variability_index(210.0, 200.0) == 1.05
    assert calc_variability_index(200.0, 200.0) == 1.0


def test_power_efficiency_factor():
    ef = calc_power_efficiency_factor(200.0, 150)
    assert round(ef, 3) == 1.333


def test_work_kj():
    # 200W 持续 3600 秒 = 720kJ
    powers = [200] * 3600
    assert calc_work_kj(powers) == 720.0


def test_work_kj_empty():
    assert calc_work_kj([]) is None


# ============================================================
# 心率衍生指标测试
# ============================================================


def test_hr_intensity_factor():
    assert calc_hr_intensity_factor(160, 160) == 1.0
    assert calc_hr_intensity_factor(140, 160) == 0.875


def _make_hr_trackpoints(duration_seconds: int, hr: int, interval: int = 1) -> list[dict]:
    """生成指定时长、恒定心率的 trackpoint 列表。"""
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    tps = []
    for s in range(0, duration_seconds + 1, interval):
        tps.append({"time": base + timedelta(seconds=s), "heart_rate": hr})
    return tps


def _make_power_trackpoints(duration_seconds: int, power: int, interval: int = 1) -> list[dict]:
    """生成指定时长、恒定功率的 trackpoint 列表。"""
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    tps = []
    for s in range(0, duration_seconds + 1, interval):
        tps.append({"time": base + timedelta(seconds=s), "power": power})
    return tps


def test_hr_tss():
    # 1 小时阈值心率骑行 = 100 TSS
    tps = _make_hr_trackpoints(3600, 160)
    tss = calc_hr_tss(tps, 160)
    assert abs(tss - 100.0) < 1.0

    # 1 小时 80% LTHR = 64 TSS
    tps = _make_hr_trackpoints(3600, 128)
    tss = calc_hr_tss(tps, 160)
    assert abs(tss - 64.0) < 1.0


def test_hr_tss_missing():
    assert calc_hr_tss([], 160) is None
    assert calc_hr_tss(_make_hr_trackpoints(10, 0), 160) is None


def test_hr_efficiency_factor():
    ef = calc_hr_efficiency_factor(8.0, 160)
    assert ef == 0.05


# ============================================================
# 功率 TSS 测试
# ============================================================


def test_power_tss():
    # 1 小时 FTP 骑行（IF=1.0）= 100 TSS
    tps = _make_power_trackpoints(3600, 250)
    tss = calc_power_tss(tps, 250)
    assert abs(tss - 100.0) < 1.0

    # 1 小时 75% IF = 56.25 TSS
    tps = _make_power_trackpoints(3600, 187)
    tss = calc_power_tss(tps, 250)
    assert abs(tss - (3600 / 3600) * (187 / 250) ** 2 * 100) < 1.0


# ============================================================
# 分区时间统计测试
# ============================================================


def test_zone_times_basic():
    hr_zones = [
        {"name": "Z1", "min": 0, "max": 120},
        {"name": "Z2", "min": 120, "max": 150},
        {"name": "Z3", "min": 150, "max": 170},
    ]
    values = [100, 130, 160, 140, 110]
    result = calc_zone_times(values, hr_zones)
    assert result["Z1"] == 2.0  # 100, 110
    assert result["Z2"] == 2.0  # 130, 140
    assert result["Z3"] == 1.0  # 160


def test_zone_times_with_none():
    hr_zones = [
        {"name": "Z1", "min": 0, "max": 150},
        {"name": "Z2", "min": 150, "max": 999},
    ]
    values = [100, None, 160, None]
    result = calc_zone_times(values, hr_zones)
    assert result["Z1"] == 1.0
    assert result["Z2"] == 1.0


# ============================================================
# 统一计算入口测试
# ============================================================


def _make_trackpoints(duration_minutes=5, power=200, hr=150, speed=8.0):
    """生成模拟 trackpoint 列表。"""
    base_time = datetime(2026, 4, 27, 8, 0, 0, tzinfo=timezone.utc)
    tps = []
    for i in range(duration_minutes * 60):
        tps.append(
            {
                "time": base_time + timedelta(seconds=i),
                "power": power,
                "heart_rate": hr,
                "speed": speed,
                "cadence": 80,
                "distance": float(i * speed),
            }
        )
    return tps


def test_compute_cycling_with_power():
    tps = _make_trackpoints(5, power=200, hr=150)
    hr_zones = [
        {"name": "Z1", "min": 0, "max": 109},
        {"name": "Z2", "min": 109, "max": 133},
        {"name": "Z3", "min": 133, "max": 150},
        {"name": "Z4", "min": 150, "max": 168},
        {"name": "Z5", "min": 168, "max": 999},
    ]
    power_zones = [
        {"name": "Z1", "min": 0, "max": 137},
        {"name": "Z2", "min": 137, "max": 187},
        {"name": "Z3", "min": 187, "max": 225},
        {"name": "Z4", "min": 225, "max": 262},
    ]

    metrics = compute_activity_metrics(
        trackpoints=tps,
        activity_type="cycling",
        hr_zones=hr_zones,
        power_zones=power_zones,
        ftp=250,
        lthr=160,
    )

    # 有功率，应使用功率 TSS
    assert metrics.tss is not None
    assert metrics.tss_method == "power"
    assert metrics.normalized_power is not None
    assert metrics.intensity_factor is not None
    assert metrics.work_kj is not None
    assert metrics.hr_zones_time is not None
    assert metrics.power_zones_time is not None


def test_compute_running_hr_tss():
    tps = _make_trackpoints(30, power=None, hr=160, speed=3.5)
    hr_zones = [
        {"name": "Z1", "min": 0, "max": 116},
        {"name": "Z2", "min": 116, "max": 141},
        {"name": "Z3", "min": 141, "max": 160},
        {"name": "Z4", "min": 160, "max": 176},
        {"name": "Z5", "min": 176, "max": 999},
    ]

    metrics = compute_activity_metrics(
        trackpoints=tps,
        activity_type="running",
        hr_zones=hr_zones,
        power_zones=[],
        lthr=170,
    )

    assert metrics.tss is None  # 跑步无功率，tss 为空
    assert metrics.hr_tss is not None  # hr_tss 有值
    assert metrics.normalized_power is None  # 无功率数据


def test_compute_no_trackpoints():
    metrics = compute_activity_metrics(
        trackpoints=[],
        activity_type="cycling",
        hr_zones=[],
        power_zones=[],
    )
    assert metrics.tss is None


# ============================================================
# PMC 测试
# ============================================================


def test_pmc_basic():
    # 7 天训练，每天 100 TSS
    daily_tss = {f"2026-04-{d:02d}": 100.0 for d in range(20, 27)}
    result = calc_pmc(daily_tss, "2026-04-20", "2026-04-26")

    assert len(result) == 7
    assert result[0]["tss"] == 100.0
    assert result[0]["ctl"] > 0
    assert result[0]["atl"] > 0
    assert result[0]["tsb"] < 0  # 初期 ATL > CTL，TSB 为负

    # 持续训练后 CTL 和 ATL 都在增长
    assert result[-1]["ctl"] > result[0]["ctl"]
    assert result[-1]["atl"] > result[0]["atl"]


def test_pmc_rest_day():
    daily_tss = {"2026-04-20": 100.0, "2026-04-21": 0.0}
    result = calc_pmc(daily_tss, "2026-04-20", "2026-04-21")

    # 休息日 TSS = 0
    assert result[1]["tss"] == 0.0
    # CTL 仍在增长（衰减慢），ATL 可能下降（衰减快）
    assert result[1]["ctl"] > 0


# ============================================================
# 跑步效率因子测试
# ============================================================


def test_running_efficiency_factor():
    """跑步活动应计算 efficiency_factor = avg_speed / avg_hr。"""
    tps = _make_trackpoints(10, power=None, hr=160, speed=3.0)
    hr_zones = [
        {"name": "Z1", "min": 0, "max": 116},
        {"name": "Z2", "min": 116, "max": 141},
        {"name": "Z3", "min": 141, "max": 160},
        {"name": "Z4", "min": 160, "max": 176},
        {"name": "Z5", "min": 176, "max": 999},
    ]
    metrics = compute_activity_metrics(
        trackpoints=tps,
        activity_type="running",
        hr_zones=hr_zones,
        power_zones=[],
        lthr=170,
    )
    assert metrics.efficiency_factor is not None
    # 3.0 / 160 = 0.01875, round(0.01875, 4) = 0.0188 (但速度平均值可能略有差异)
    assert abs(metrics.efficiency_factor - 0.0188) < 0.001


def test_cycling_ef_unchanged():
    """骑行活动的 efficiency_factor 仍基于功率 NP/avgHR。"""
    tps = _make_trackpoints(10, power=200, hr=150, speed=8.0)
    power_zones = [
        {"name": "Z1", "min": 0, "max": 137},
        {"name": "Z2", "min": 137, "max": 187},
        {"name": "Z3", "min": 187, "max": 225},
    ]
    metrics = compute_activity_metrics(
        trackpoints=tps,
        activity_type="cycling",
        hr_zones=[],
        power_zones=power_zones,
        ftp=250,
        lthr=160,
    )
    assert metrics.efficiency_factor is not None
    assert metrics.efficiency_factor > 1.0  # NP/HR, NP~200, HR=150 → >1.0


# ============================================================
# 配速最佳表现测试
# ============================================================


def _make_running_trackpoints(distance_meters=10000, speed_mps=3.0, hr=160):
    """生成模拟跑步 trackpoint 列表。"""
    base_time = datetime(2026, 5, 1, 8, 0, 0, tzinfo=timezone.utc)
    interval = 1  # 每秒一个点
    tps = []
    for i in range(int(distance_meters / speed_mps) + 1):
        tps.append(
            {
                "time": base_time + timedelta(seconds=i),
                "heart_rate": hr,
                "speed": speed_mps,
                "cadence": 180,
                "distance": float(i * speed_mps),
            }
        )
    return tps


def test_pace_best_efforts_constant_speed():
    """匀速跑步，所有距离的最佳配速应接近实际配速。"""
    speed = 3.0  # 3 m/s = 5:33 /km
    tps = _make_running_trackpoints(distance_meters=12000, speed_mps=speed)
    result = calc_pace_best_efforts(tps)

    assert "1000" in result
    assert "5000" in result
    assert "10000" in result

    # 预期配速 = 1000 / 3.0 ≈ 333.3 秒/公里
    expected_pace = 1000 / speed
    for dist, pace in result.items():
        assert abs(pace - expected_pace) < 10, f"Distance {dist}: pace {pace} vs expected {expected_pace}"


def test_pace_best_efforts_empty():
    assert calc_pace_best_efforts([]) == {}
    assert calc_pace_best_efforts([{"time": datetime(2026, 1, 1, tzinfo=timezone.utc)}]) == {}


def test_pace_best_efforts_short_distance():
    """距离不够的活动不应返回长距离的最佳配速。"""
    tps = _make_running_trackpoints(distance_meters=3000, speed_mps=3.0)
    result = calc_pace_best_efforts(tps)

    assert "400" in result
    assert "1000" in result
    assert "3000" in result
    assert "5000" not in result  # 总距离不足 5km


# ============================================================
# 坡度调整配速测试
# ============================================================


def test_grade_adjusted_pace_uphill():
    """上坡 5% 应使 GAP 速度低于实际速度。"""
    gap = calc_grade_adjusted_pace(3.0, 5.0)
    assert gap is not None
    assert gap < 3.0  # 上坡等效速度更慢


def test_grade_adjusted_pace_downhill():
    """下坡 -5% 应使 GAP 速度高于实际速度。"""
    gap = calc_grade_adjusted_pace(3.0, -5.0)
    assert gap is not None
    assert gap > 3.0  # 下坡等效速度更快


def test_grade_adjusted_pace_flat():
    """平地 grade=0，GAP 速度等于实际速度。"""
    gap = calc_grade_adjusted_pace(3.0, 0.0)
    assert gap == 3.0


def test_grade_adjusted_pace_zero_speed():
    assert calc_grade_adjusted_pace(0, 5.0) is None
    assert calc_grade_adjusted_pace(-1, 5.0) is None


# ============================================================
# 跑步完整指标测试
# ============================================================


def test_compute_running_full_metrics():
    """跑步活动应包含 hr_tss、hr_intensity_factor、efficiency_factor、pace_best_efforts。"""
    tps = _make_running_trackpoints(distance_meters=12000, speed_mps=3.0, hr=165)
    hr_zones = [
        {"name": "Z1", "min": 0, "max": 116},
        {"name": "Z2", "min": 116, "max": 141},
        {"name": "Z3", "min": 141, "max": 160},
        {"name": "Z4", "min": 160, "max": 179},
        {"name": "Z5", "min": 179, "max": 999},
    ]
    metrics = compute_activity_metrics(
        trackpoints=tps,
        activity_type="running",
        hr_zones=hr_zones,
        power_zones=[],
        lthr=170,
    )

    assert metrics.tss is None  # 无功率 TSS
    assert metrics.hr_tss is not None
    assert metrics.hr_intensity_factor is not None
    assert metrics.efficiency_factor is not None
    assert metrics.pace_best_efforts is not None
    assert "1000" in metrics.pace_best_efforts
    assert "5000" in metrics.pace_best_efforts
    assert "10000" in metrics.pace_best_efforts
    assert metrics.intensity_level is not None
