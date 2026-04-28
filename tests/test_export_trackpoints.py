import io

import pytest

from tests.test_upload_api import MINIMAL_TCX


def _upload_sample(client, auth_headers, activity_type="cycling", name="测试"):
    data = {
        "file": (io.BytesIO(MINIMAL_TCX.encode()), "test.tcx"),
        "activity_type": activity_type,
        "name": name,
    }
    resp = client.post("/api/activities/upload", data=data, headers=auth_headers, content_type="multipart/form-data")
    return resp.get_json()["data"]


def test_export_csv(client, auth_headers):
    _upload_sample(client, auth_headers, "cycling", "骑行1")
    _upload_sample(client, auth_headers, "running", "跑步1")

    resp = client.get("/api/activities/export")
    assert resp.status_code == 200
    assert resp.content_type == "text/csv; charset=utf-8"
    text = resp.data.decode("utf-8")
    lines = text.strip().split("\n")
    # 1 header + 2 data rows
    assert len(lines) == 3
    assert "日期" in lines[0]
    assert "TSS" in lines[0]


def test_export_csv_with_type_filter(client, auth_headers):
    _upload_sample(client, auth_headers, "cycling", "骑行")
    _upload_sample(client, auth_headers, "running", "跑步")

    resp = client.get("/api/activities/export?activity_type=cycling")
    assert resp.status_code == 200
    lines = resp.data.decode("utf-8").strip().split("\n")
    assert len(lines) == 2  # header + 1 row


def test_export_csv_empty(client):
    resp = client.get("/api/activities/export")
    assert resp.status_code == 200
    lines = resp.data.decode("utf-8").strip().split("\n")
    assert len(lines) == 1  # only header


def test_get_trackpoints(client, auth_headers):
    uploaded = _upload_sample(client, auth_headers)
    activity_id = uploaded["id"]

    resp = client.get(f"/api/activities/{activity_id}/trackpoints")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert "total_points" in data
    assert "points" in data
    assert data["total_points"] >= 0


def test_get_trackpoints_not_found(client):
    resp = client.get("/api/activities/000000000000000000000000/trackpoints")
    assert resp.status_code == 404


def test_get_trackpoints_max_points(client, auth_headers):
    uploaded = _upload_sample(client, auth_headers)
    activity_id = uploaded["id"]

    resp = client.get(f"/api/activities/{activity_id}/trackpoints?max_points=10")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert len(data["points"]) <= 10


def test_export_json(client, auth_headers):
    _upload_sample(client, auth_headers, "cycling", "骑行1")
    _upload_sample(client, auth_headers, "running", "跑步1")

    resp = client.get("/api/activities/export?format=json")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["code"] == 200
    assert len(data["data"]) == 2
    names = [d["name"] for d in data["data"]]
    assert "骑行1" in names
    assert "跑步1" in names


def test_export_json_with_filter(client, auth_headers):
    _upload_sample(client, auth_headers, "cycling", "骑行")
    _upload_sample(client, auth_headers, "running", "跑步")

    resp = client.get("/api/activities/export?format=json&activity_type=running")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["data"]) == 1
    assert data["data"][0]["activity_type"] == "running"


def test_export_csv_has_intensity_column(client, auth_headers):
    _upload_sample(client, auth_headers)
    resp = client.get("/api/activities/export")
    lines = resp.data.decode("utf-8").strip().split("\n")
    assert "强度" in lines[0]
