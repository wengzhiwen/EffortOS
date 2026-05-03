from datetime import datetime, timedelta

from app.services.metrics_service import calc_lap_splits


def _make_trackpoints(count, interval=1.0, distance_step=10.0, base_power=200, base_hr=150):
    """生成测试用 trackpoint 列表。"""
    base = datetime(2026, 5, 3, 10, 0, 0)
    tps = []
    for i in range(count):
        tps.append(
            {
                "time": base + timedelta(seconds=i * interval),
                "distance": i * distance_step,
                "heart_rate": base_hr + (i % 10),
                "power": base_power + (i % 5),
                "speed": distance_step / interval,
                "cadence": 90,
                "altitude": 100 + i * 0.1,
            }
        )
    return tps


def test_empty_trackpoints():
    assert calc_lap_splits([]) == []


def test_single_trackpoint():
    tps = _make_trackpoints(1)
    assert calc_lap_splits(tps) == []


def test_distance_splits():
    """每 100 米分段。"""
    # 500 米，每秒 10 米 → 50 秒
    tps = _make_trackpoints(50, distance_step=10.0)
    laps = calc_lap_splits(tps, mode="distance", interval=100)
    assert len(laps) == 5
    for lap in laps:
        assert lap["distance_meters"] > 0
        assert lap["duration_seconds"] > 0
        assert lap["avg_speed_kmh"] is not None


def test_time_splits():
    """每 10 秒分段。"""
    # 50 个点，每秒 1 个
    tps = _make_trackpoints(50, interval=1.0, distance_step=10.0)
    laps = calc_lap_splits(tps, mode="time", interval=10)
    assert len(laps) >= 4  # 应有约 5 段
    for lap in laps:
        assert lap["avg_hr"] is not None
        assert lap["avg_power"] is not None


def test_last_lap_included():
    """最后不足一段的部分也应被包含。"""
    # 250 米 → 前 2 段 100m + 最后 50m
    tps = _make_trackpoints(25, distance_step=10.0)
    laps = calc_lap_splits(tps, mode="distance", interval=100)
    assert len(laps) == 3
    assert laps[-1]["distance_meters"] < 100


def test_lap_stats_fields():
    """每段统计应包含所有预期字段。"""
    tps = _make_trackpoints(30, distance_step=10.0)
    laps = calc_lap_splits(tps, mode="distance", interval=100)
    assert len(laps) >= 1
    lap = laps[0]
    assert "lap" in lap
    assert "start_elapsed" in lap
    assert "end_elapsed" in lap
    assert "duration_seconds" in lap
    assert "distance_meters" in lap
    assert "avg_speed_kmh" in lap
    assert "avg_hr" in lap
    assert "max_hr" in lap
    assert "avg_power" in lap
    assert "max_power" in lap
    assert "avg_cadence" in lap


def test_no_distance_data():
    """无距离数据时按距离分段：无法达到 boundary，只有最后尾部段。"""
    tps = []
    base = datetime(2026, 5, 3, 10, 0, 0)
    for i in range(100):
        tps.append(
            {
                "time": base + timedelta(seconds=i),
                "distance": None,
                "heart_rate": 150,
                "power": 200,
            }
        )
    laps = calc_lap_splits(tps, mode="distance", interval=100)
    # 距离全为 None，无法达到 boundary，最后段被包含
    assert len(laps) == 1
    assert laps[0]["avg_speed_kmh"] is None


def test_speed_calculation():
    """验证配速计算。"""
    # 10 秒跑 100 米 → 36 km/h
    tps = _make_trackpoints(10, interval=1.0, distance_step=10.0)
    laps = calc_lap_splits(tps, mode="distance", interval=100)
    if laps:
        assert abs(laps[0]["avg_speed_kmh"] - 36.0) < 1.0
