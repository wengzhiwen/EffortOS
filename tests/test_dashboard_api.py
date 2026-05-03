import io
from datetime import datetime

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


def test_dashboard_no_auth(client):
    """未登录用户也应能获取空 dashboard。"""
    resp = client.get("/api/dashboard")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["ctl"] == 0
    assert data["recent_activities"] == []


def test_dashboard_weekly_trend(client, auth_headers):
    """周趋势数据结构正确。"""
    _upload_activity(client, auth_headers)
    resp = client.get("/api/dashboard", headers=auth_headers)
    data = resp.get_json()["data"]
    trend = data["weekly_trend"]
    assert isinstance(trend, list)
    assert len(trend) == 12
    assert "week" in trend[0]
    assert "tss" in trend[0]
    assert "count" in trend[0]


def test_dashboard_calendar_structure(client, auth_headers):
    """日历数据为 dict 且 key 为日期格式。"""
    _upload_activity(client, auth_headers)
    resp = client.get("/api/dashboard", headers=auth_headers)
    data = resp.get_json()["data"]
    cal = data["calendar"]
    assert isinstance(cal, dict)
    for key in cal:
        assert len(key) == 10  # YYYY-MM-DD


def test_pmc_date_range_invalid(client):
    """PMC 无效日期格式应返回 400。"""
    resp = client.get("/api/pmc?start_date=not-a-date&end_date=also-bad")
    assert resp.status_code == 400
