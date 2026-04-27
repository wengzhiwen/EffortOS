import io
import pytest


def _upload_sample(client, activity_type="cycling", name="测试"):
    """辅助函数：上传一个示例活动。"""
    from tests.test_upload_api import MINIMAL_TCX

    data = {
        "file": (io.BytesIO(MINIMAL_TCX.encode()), "test.tcx"),
        "activity_type": activity_type,
        "name": name,
    }
    resp = client.post("/api/activities/upload", data=data, content_type="multipart/form-data")
    return resp.get_json()["data"]


def test_list_activities_empty(client):
    resp = client.get("/api/activities")
    assert resp.status_code == 200
    result = resp.get_json()
    assert result["data"]["total"] == 0
    assert result["data"]["items"] == []


def test_list_activities_after_upload(client):
    _upload_sample(client, "cycling", "骑行1")
    _upload_sample(client, "running", "跑步1")

    resp = client.get("/api/activities")
    result = resp.get_json()
    assert result["data"]["total"] == 2


def test_list_activities_filter_by_type(client):
    _upload_sample(client, "cycling", "骑行")
    _upload_sample(client, "running", "跑步")

    resp = client.get("/api/activities?activity_type=cycling")
    result = resp.get_json()
    assert result["data"]["total"] == 1
    assert result["data"]["items"][0]["activity_type"] == "cycling"


def test_list_activities_pagination(client):
    for i in range(5):
        _upload_sample(client, "cycling", f"骑行{i}")

    resp = client.get("/api/activities?limit=2&offset=0")
    result = resp.get_json()
    assert len(result["data"]["items"]) == 2
    assert result["data"]["total"] == 5

    resp2 = client.get("/api/activities?limit=2&offset=2")
    result2 = resp2.get_json()
    assert len(result2["data"]["items"]) == 2


def test_get_activity(client):
    uploaded = _upload_sample(client)
    activity_id = uploaded["id"]

    resp = client.get(f"/api/activities/{activity_id}")
    assert resp.status_code == 200
    result = resp.get_json()
    assert result["data"]["id"] == activity_id
    assert result["data"]["name"] == "测试"


def test_get_activity_not_found(client):
    resp = client.get("/api/activities/000000000000000000000000")
    assert resp.status_code == 404


def test_delete_activity(client):
    uploaded = _upload_sample(client)
    activity_id = uploaded["id"]

    resp = client.delete(f"/api/activities/{activity_id}")
    assert resp.status_code == 200

    # 确认已删除
    resp2 = client.get(f"/api/activities/{activity_id}")
    assert resp2.status_code == 404


def test_delete_activity_not_found(client):
    resp = client.delete("/api/activities/000000000000000000000000")
    assert resp.status_code == 404
