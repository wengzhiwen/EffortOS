import io


def _upload_sample(client, auth_headers, activity_type="cycling", name="测试"):
    """辅助函数：上传一个示例活动。"""
    from tests.test_upload_api import MINIMAL_TCX

    data = {
        "file": (io.BytesIO(MINIMAL_TCX.encode()), "test.tcx"),
        "activity_type": activity_type,
        "name": name,
    }
    resp = client.post("/api/activities/upload", data=data, headers=auth_headers, content_type="multipart/form-data")
    return resp.get_json()["data"]


def test_list_activities_empty(client):
    resp = client.get("/api/activities")
    assert resp.status_code == 200
    result = resp.get_json()
    assert result["data"]["total"] == 0
    assert result["data"]["items"] == []


def test_list_activities_after_upload(client, auth_headers):
    _upload_sample(client, auth_headers, "cycling", "骑行1")
    _upload_sample(client, auth_headers, "running", "跑步1")

    resp = client.get("/api/activities")
    result = resp.get_json()
    assert result["data"]["total"] == 2


def test_list_activities_filter_by_type(client, auth_headers):
    _upload_sample(client, auth_headers, "cycling", "骑行")
    _upload_sample(client, auth_headers, "running", "跑步")

    resp = client.get("/api/activities?activity_type=cycling")
    result = resp.get_json()
    assert result["data"]["total"] == 1
    assert result["data"]["items"][0]["activity_type"] == "cycling"


def test_list_activities_pagination(client, auth_headers):
    for i in range(5):
        _upload_sample(client, auth_headers, "cycling", f"骑行{i}")

    resp = client.get("/api/activities?limit=2&offset=0")
    result = resp.get_json()
    assert len(result["data"]["items"]) == 2
    assert result["data"]["total"] == 5

    resp2 = client.get("/api/activities?limit=2&offset=2")
    result2 = resp2.get_json()
    assert len(result2["data"]["items"]) == 2


def test_get_activity(client, auth_headers):
    uploaded = _upload_sample(client, auth_headers)
    activity_id = uploaded["id"]

    resp = client.get(f"/api/activities/{activity_id}")
    assert resp.status_code == 200
    result = resp.get_json()
    assert result["data"]["id"] == activity_id
    assert result["data"]["name"] == "测试"


def test_get_activity_not_found(client):
    resp = client.get("/api/activities/000000000000000000000000")
    assert resp.status_code == 404


def test_delete_activity(client, auth_headers):
    uploaded = _upload_sample(client, auth_headers)
    activity_id = uploaded["id"]

    resp = client.delete(f"/api/activities/{activity_id}", headers=auth_headers)
    assert resp.status_code == 200

    # 确认已删除
    resp2 = client.get(f"/api/activities/{activity_id}")
    assert resp2.status_code == 404


def test_delete_activity_not_found(client, auth_headers):
    resp = client.delete("/api/activities/000000000000000000000000", headers=auth_headers)
    assert resp.status_code == 404


def test_delete_no_auth(client, auth_headers):
    resp = client.delete("/api/activities/000000000000000000000000")
    assert resp.status_code == 401


def test_update_activity(client, auth_headers):
    from tests.test_upload_api import MINIMAL_TCX

    """测试更新活动名称。"""
    # 先上传一个活动
    data = {
        "file": (io.BytesIO(MINIMAL_TCX.encode()), "test.tcx"),
        "activity_type": "cycling",
        "name": "原始名称",
    }
    resp = client.post("/api/activities/upload", data=data, headers=auth_headers, content_type="multipart/form-data")
    activity_id = resp.get_json()["data"]["id"]

    # 更新名称
    resp = client.put(
        f"/api/activities/{activity_id}",
        json={"name": "更新后名称"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    result = resp.get_json()
    assert result["data"]["name"] == "更新后名称"


def test_update_activity_no_auth(client, auth_headers):
    """测试未认证更新。"""
    resp = client.put("/api/activities/000000000000000000000000", json={"name": "test"})
    assert resp.status_code == 401


def test_update_activity_invalid_type(client, auth_headers):
    from tests.test_upload_api import MINIMAL_TCX

    """测试更新无效运动类型。"""
    data = {
        "file": (io.BytesIO(MINIMAL_TCX.encode()), "test.tcx"),
        "activity_type": "cycling",
    }
    resp = client.post("/api/activities/upload", data=data, headers=auth_headers, content_type="multipart/form-data")
    activity_id = resp.get_json()["data"]["id"]

    resp = client.put(
        f"/api/activities/{activity_id}",
        json={"activity_type": "skydiving"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_list_activities_search_by_name(client, auth_headers):
    _upload_sample(client, auth_headers, "cycling", "周末长距离骑行")
    _upload_sample(client, auth_headers, "running", "晨跑5公里")

    # 搜索"骑行"应只匹配第一个
    resp = client.get("/api/activities?search=骑行")
    result = resp.get_json()
    assert result["data"]["total"] == 1
    assert "骑行" in result["data"]["items"][0]["name"]

    # 搜索不存在的关键词应返回空
    resp2 = client.get("/api/activities?search=游泳")
    result2 = resp2.get_json()
    assert result2["data"]["total"] == 0

    # 不区分大小写搜索
    _upload_sample(client, auth_headers, "cycling", "FTP Test Ride")
    resp3 = client.get("/api/activities?search=ftp")
    result3 = resp3.get_json()
    assert result3["data"]["total"] == 1



def _get_user(client, auth_headers):
    from app.models.user import User

    token = auth_headers["Authorization"].replace("Bearer ", "")
    return User.objects(session_token=token).first()
