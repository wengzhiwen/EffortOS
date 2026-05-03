import pytest

from app.models.activity import Activity, ComputedMetrics, DataSummary, Trackpoint
from app.models.user import User

from datetime import datetime, timezone


def _make_activity(user, tss=50, best_efforts=None, start_time=None):
    cm = ComputedMetrics()
    cm.tss = tss
    cm.tss_method = "power"
    if best_efforts:
        cm.best_efforts = best_efforts

    summary = DataSummary()
    summary.duration_seconds = 3600
    summary.total_distance = 40000

    a = Activity(
        user=user,
        name="测试",
        activity_type="cycling",
        start_time=start_time or datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc),
    )
    a.data_summary = summary
    a.computed_metrics = cm
    a.save()
    return a


def test_power_curve_no_auth(client):
    resp = client.get("/api/activities/power-curve")
    assert resp.status_code == 401


def test_power_curve_empty(client, auth_headers):
    resp = client.get("/api/activities/power-curve", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["power"] == {}
    assert data["heart_rate"] == {}


def test_power_curve_with_data(client, auth_headers):
    user = _get_user(client, auth_headers)
    _make_activity(user, best_efforts={"power": {"5": 400, "60": 300}, "heart_rate": {"5": 180, "60": 165}})
    _make_activity(
        user,
        best_efforts={"power": {"5": 420, "60": 280}, "heart_rate": {"5": 175, "60": 170}},
        start_time=datetime(2026, 5, 2, 10, 0, 0, tzinfo=timezone.utc),
    )

    resp = client.get("/api/activities/power-curve", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    # 5s peak should be max of 400, 420
    assert data["power"]["5"] == 420
    # 60s peak should be max of 300, 280
    assert data["power"]["60"] == 300
    assert data["heart_rate"]["5"] == 180
    assert data["heart_rate"]["60"] == 170


def test_power_curve_sorted_by_window(client, auth_headers):
    user = _get_user(client, auth_headers)
    _make_activity(user, best_efforts={"power": {"300": 200, "5": 500, "60": 350}})

    resp = client.get("/api/activities/power-curve", headers=auth_headers)
    data = resp.get_json()["data"]
    keys = list(data["power"].keys())
    assert keys == sorted(keys, key=lambda x: int(x))


def _get_user(client, auth_headers):
    token = auth_headers["Authorization"].replace("Bearer ", "")
    return User.objects(session_token=token).first()
