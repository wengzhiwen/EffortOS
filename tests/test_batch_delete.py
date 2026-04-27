import io

from tests.test_upload_api import MINIMAL_TCX


def _upload(client, auth_headers, name="测试"):
    data = {
        "file": (io.BytesIO(MINIMAL_TCX.encode()), "test.tcx"),
        "activity_type": "cycling",
        "name": name,
    }
    resp = client.post("/api/activities/upload", data=data, headers=auth_headers, content_type="multipart/form-data")
    return resp.get_json()["data"]["id"]


def test_batch_delete(client, auth_headers):
    id1 = _upload(client, auth_headers, "活动1")
    id2 = _upload(client, auth_headers, "活动2")
    id3 = _upload(client, auth_headers, "活动3")

    resp = client.post(
        "/api/activities/batch-delete",
        json={"ids": [id1, id3]},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    result = resp.get_json()
    assert result["data"]["deleted"] == 2

    # 验证只有 id2 还在
    resp = client.get("/api/activities")
    items = resp.get_json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["id"] == id2


def test_batch_delete_no_auth(client):
    resp = client.post("/api/activities/batch-delete", json={"ids": ["fake"]})
    assert resp.status_code == 401


def test_batch_delete_missing_ids(client, auth_headers):
    resp = client.post("/api/activities/batch-delete", json={}, headers=auth_headers)
    assert resp.status_code == 400


def test_batch_delete_empty_ids(client, auth_headers):
    resp = client.post("/api/activities/batch-delete", json={"ids": []}, headers=auth_headers)
    assert resp.status_code == 400


def test_batch_delete_too_many(client, auth_headers):
    ids = [f"00000000000000000000000{i}" for i in range(51)]
    resp = client.post("/api/activities/batch-delete", json={"ids": ids}, headers=auth_headers)
    assert resp.status_code == 400
