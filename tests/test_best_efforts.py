from datetime import datetime, timedelta

from app.services.metrics_service import BEST_EFFORT_WINDOWS, calc_best_efforts


def _make_trackpoints(seconds, power=None, hr=None):
    """生成测试用 trackpoint 列表。"""
    base = datetime(2026, 5, 3, 10, 0, 0)
    tps = []
    for i in range(seconds):
        tp = {"time": base + timedelta(seconds=i)}
        if power is not None:
            tp["power"] = power if isinstance(power, int) else power(i)
        if hr is not None:
            tp["heart_rate"] = hr if isinstance(hr, int) else hr(i)
        tps.append(tp)
    return tps


def test_empty_trackpoints():
    assert calc_best_efforts([]) == {}


def test_single_trackpoint():
    tps = _make_trackpoints(1, power=200, hr=150)
    assert calc_best_efforts(tps) == {}


def test_constant_power():
    tps = _make_trackpoints(120, power=200, hr=150)
    result = calc_best_efforts(tps)
    assert "power" in result
    assert "heart_rate" in result
    for val in result["power"].values():
        assert val == 200
    for val in result["heart_rate"].values():
        assert val == 150


def test_keys_are_strings():
    """MongoEngine DictField 要求 key 为字符串。"""
    tps = _make_trackpoints(120, power=200, hr=150)
    result = calc_best_efforts(tps)
    for key in result.get("power", {}):
        assert isinstance(key, str)
    for key in result.get("heart_rate", {}):
        assert isinstance(key, str)


def test_peak_power_short_window():
    """前 10 秒高功率，后面低功率 — 短窗口应捕获峰值。"""

    def power_fn(i):
        return 400 if i < 10 else 150

    tps = _make_trackpoints(120, power=power_fn, hr=150)
    result = calc_best_efforts(tps)
    assert result["power"]["5"] > 300
    assert result["power"]["60"] < 200


def test_increasing_power():
    """功率逐渐增加 — 长窗口平均值应低于短窗口。"""

    def power_fn(i):
        return 100 + i

    tps = _make_trackpoints(600, power=power_fn)
    result = calc_best_efforts(tps)
    assert result["power"]["5"] > result["power"]["300"]


def test_windows_capped_by_data_length():
    """数据不足的窗口不应出现。"""
    tps = _make_trackpoints(10, power=200)
    result = calc_best_efforts(tps)
    if "power" in result:
        for w in result["power"]:
            assert int(w) <= 20


def test_only_power_no_hr():
    """只有功率数据时不应返回心率。"""
    tps = _make_trackpoints(120, power=200)
    result = calc_best_efforts(tps)
    assert "power" in result
    assert "heart_rate" not in result


def test_only_hr_no_power():
    """只有心率数据时不应返回功率。"""
    tps = _make_trackpoints(120, hr=150)
    result = calc_best_efforts(tps)
    assert "heart_rate" in result
    assert "power" not in result


def test_long_activity_all_windows():
    """3600 秒活动应覆盖所有窗口。"""
    tps = _make_trackpoints(3600, power=200, hr=150)
    result = calc_best_efforts(tps)
    assert "power" in result
    for w in BEST_EFFORT_WINDOWS:
        assert str(w) in result["power"], f"窗口 {w} 未出现在结果中"


def test_sprint_effort():
    """模拟冲刺：中间 15 秒极高功率。"""

    def power_fn(i):
        return 600 if 500 <= i < 515 else 200

    tps = _make_trackpoints(1000, power=power_fn)
    result = calc_best_efforts(tps)
    assert result["power"]["5"] >= 550
    assert result["power"]["15"] >= 550
    assert result["power"]["300"] < 300
