import io
from datetime import datetime

import pytest

from tests.test_upload_api import MINIMAL_TCX

_today = datetime.now().strftime("%Y-%m-%d")


def _upload_activity(client, auth_headers, activity_type="cycling", name="测试"):
    data = {
        "file": (io.BytesIO(MINIMAL_TCX.encode()), "test.tcx"),
        "activity_type": activity_type,
        "name": name,
    }
    resp = client.post("/api/activities/upload", data=data, headers=auth_headers, content_type="multipart/form-data")
    return resp.get_json()["data"]


def _save_params(client, auth_headers, ftp=200, lthr=160):
    client.post(
        "/api/params",
        json={
            "effective_date": _today,
            "ftp": ftp,
            "cycling_lthr": lthr,
            "running_lthr": 170,
            "max_heart_rate": 190,
        },
        headers=auth_headers,
    )


def test_pmc_empty(client):
    resp = client.get("/api/pmc")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert isinstance(data, list)


def test_pmc_with_activities(client, auth_headers):
    _upload_activity(client, auth_headers)
    resp = client.get("/api/pmc")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert len(data) > 0
    assert "date" in data[0]
    assert "ctl" in data[0]
    assert "atl" in data[0]
    assert "tsb" in data[0]


def test_pmc_date_range(client, auth_headers):
    start = "2026-04-01"
    end = "2026-04-27"
    resp = client.get(f"/api/pmc?start_date={start}&end_date={end}")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert len(data) == 27


def test_dashboard_empty(client):
    resp = client.get("/api/dashboard")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["ctl"] == 0
    assert data["atl"] == 0
    assert data["tsb"] == 0
    assert data["recent_activities"] == []


def test_dashboard_with_activities(client, auth_headers):
    _upload_activity(client, auth_headers, "cycling", "骑行1")
    _upload_activity(client, auth_headers, "running", "跑步1")

    resp = client.get("/api/dashboard", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert len(data["recent_activities"]) == 2
    assert "pmc" in data
    assert "calendar" in data
    assert "weekly_stats" in data
    assert "monthly_stats" in data
    assert "type_breakdown" in data
    assert data["type_breakdown"]["cycling"] == 1
    assert data["type_breakdown"]["running"] == 1


def test_dashboard_stats_values(client, auth_headers):
    _save_params(client, auth_headers)
    _upload_activity(client, auth_headers)

    resp = client.get("/api/dashboard", headers=auth_headers)
    data = resp.get_json()["data"]
    stats = data["monthly_stats"]
    assert stats["count"] == 1
    assert "total_duration_minutes" in stats
    assert "total_distance_km" in stats
