import pytest

from app.models.activity import Activity, ComputedMetrics, DataSummary, Trackpoint
from app.models.user import User


@pytest.fixture
def app():
    import os

    os.environ["FLASK_ENV"] = "testing"
    from app import create_app

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


def _make_activity_with_tps(duration=120, power=200, hr=150):
    from datetime import datetime, timezone

    tps = []
    for i in range(duration):
        tp = Trackpoint(elapsed=float(i))
        tp.hr = hr + (i % 10)
        tp.power = power + (i % 5)
        tp.speed = 8.0
        tp.distance = 960 * i / duration
        tp.altitude = 100 + (i % 20)
        tps.append(tp)

    summary = DataSummary()
    summary.duration_seconds = duration
    summary.total_distance = 960

    activity = Activity(
        name="测试活动",
        activity_type="cycling",
        start_time=datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc),
    )
    activity.data_summary = summary
    activity.trackpoints = tps
    activity.save()
    return activity


def test_get_trackpoints(client):
    a = _make_activity_with_tps(duration=100)

    resp = client.get(f"/api/activities/{a.id}/trackpoints")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["total_points"] == 100
    assert len(data["points"]) > 0
    assert "elapsed" in data["points"][0]


def test_get_trackpoints_downsampled(client):
    a = _make_activity_with_tps(duration=500)

    resp = client.get(f"/api/activities/{a.id}/trackpoints?max_points=50")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["total_points"] == 500
    assert len(data["points"]) <= 50


def test_get_trackpoints_not_found(client):
    from bson import ObjectId

    resp = client.get(f"/api/activities/{ObjectId()}/trackpoints")
    assert resp.status_code == 404


def test_get_lap_splits(client):
    a = _make_activity_with_tps(duration=300)

    resp = client.get(f"/api/activities/{a.id}/laps?mode=distance&interval=500")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert isinstance(data, list)


def test_get_lap_splits_time_mode(client):
    a = _make_activity_with_tps(duration=300)

    resp = client.get(f"/api/activities/{a.id}/laps?mode=time&interval=60")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert isinstance(data, list)
    if len(data) > 0:
        assert "avg_hr" in data[0]


def test_get_lap_splits_not_found(client):
    from bson import ObjectId

    resp = client.get(f"/api/activities/{ObjectId()}/laps")
    assert resp.status_code == 404


def test_get_activity_serialization(client):
    a = _make_activity_with_tps(duration=60)

    resp = client.get(f"/api/activities/{a.id}")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["name"] == "测试活动"
    assert data["activity_type"] == "cycling"
    assert data["data_summary"]["duration_seconds"] == 60
    assert data["data_summary"]["total_distance"] == 960
