import os

import pytest

from app import create_app
from app.models.activity import Activity, ComputedMetrics, DataSummary, Trackpoint
from app.models.user import User

MINIMAL_TCX = os.path.join(os.path.dirname(__file__), "..", "samples", "minimal.tcx")


@pytest.fixture
def app():
    os.environ["FLASK_ENV"] = "testing"
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_db(app):
    with app.app_context():
        User.drop_collection()
        Activity.drop_collection()


def _make_activity(name, duration=120, power=200, hr=150, speed=8.0, distance=960):
    """创建一个带 trackpoints 的测试活动。"""
    from datetime import datetime, timezone

    tps = []
    for i in range(duration):
        tp = Trackpoint(elapsed=float(i))
        tp.hr = hr + (i % 10)
        tp.power = power + (i % 5)
        tp.speed = speed
        tp.distance = distance * i / duration
        tps.append(tp)

    summary = DataSummary()
    summary.duration_seconds = duration
    summary.total_distance = distance
    summary.avg_heart_rate = hr
    summary.max_heart_rate = hr + 20
    summary.avg_power = power
    summary.max_power = power + 50

    metrics = ComputedMetrics()
    metrics.tss = duration * 0.5
    metrics.intensity_factor = 0.75

    activity = Activity(
        name=name,
        activity_type="cycling",
        start_time=datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc),
    )
    activity.data_summary = summary
    activity.computed_metrics = metrics
    activity.trackpoints = tps
    activity.save()
    return activity


class TestCompareAPI:
    def test_missing_params(self, client):
        r = client.get("/api/activities/compare")
        assert r.status_code == 400
        data = r.get_json()
        assert "a" in data["message"] or "ID" in data["message"]

    def test_missing_one_param(self, client):
        r = client.get("/api/activities/compare?a=abc")
        assert r.status_code == 400

    def test_activity_not_found(self, client):
        r = client.get("/api/activities/compare?a=000000000000000000000000&b=000000000000000000000001")
        assert r.status_code == 404

    def test_compare_success(self, client):
        a = _make_activity("骑行A", duration=120, power=200)
        b = _make_activity("骑行B", duration=180, power=220)

        r = client.get(f"/api/activities/compare?a={a.id}&b={b.id}")
        assert r.status_code == 200
        data = r.get_json()["data"]

        assert data["a"]["name"] == "骑行A"
        assert data["b"]["name"] == "骑行B"
        assert data["a"]["summary"]["duration_seconds"] == 120
        assert data["b"]["summary"]["duration_seconds"] == 180
        assert len(data["a"]["trackpoints"]) > 0
        assert len(data["b"]["trackpoints"]) > 0
        # trackpoints 应包含 percent 字段
        assert "percent" in data["a"]["trackpoints"][0]

    def test_compare_same_activity(self, client):
        a = _make_activity("同一活动", duration=120)
        r = client.get(f"/api/activities/compare?a={a.id}&b={a.id}")
        assert r.status_code == 200
        data = r.get_json()["data"]
        assert data["a"]["id"] == data["b"]["id"]

    def test_compare_with_metrics(self, client):
        a = _make_activity("活动1", duration=300, power=250)
        b = _make_activity("活动2", duration=300, power=200)

        r = client.get(f"/api/activities/compare?a={a.id}&b={b.id}")
        assert r.status_code == 200
        data = r.get_json()["data"]
        assert data["a"]["metrics"]["tss"] is not None
        assert data["b"]["metrics"]["tss"] is not None
