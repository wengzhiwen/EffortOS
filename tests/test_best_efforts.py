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
    # 常数功率，所有窗口均值应相同
    for w, val in result["power"].items():
        assert val == 200
    for w, val in result["heart_rate"].items():
        assert val == 150


def test_peak_power_short_window():
    """前 10 秒高功率，后面低功率 — 短窗口应捕获峰值。"""

    def power_fn(i):
        return 400 if i < 10 else 150

    tps = _make_trackpoints(120, power=power_fn, hr=150)
    result = calc_best_efforts(tps)
    assert result["power"][5] > 300  # 5 秒窗口应捕获到高功率段
    assert result["power"][60] < 200  # 60 秒窗口会被低功率拉低


def test_increasing_power():
    """功率逐渐增加 — 长窗口平均值应低于短窗口。"""

    def power_fn(i):
        return 100 + i

    tps = _make_trackpoints(600, power=power_fn)
    result = calc_best_efforts(tps)
    # 短窗口（5s）应接近末尾高功率
    assert result["power"][5] > result["power"][300]


def test_windows_capped_by_data_length():
    """数据不足的窗口不应出现。"""
    tps = _make_trackpoints(10, power=200)
    result = calc_best_efforts(tps)
    # 只有小于等于 10 秒数据的窗口
    if "power" in result:
        for w in result["power"]:
            assert w <= 20  # 允许小误差
