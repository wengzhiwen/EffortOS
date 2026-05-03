from datetime import datetime

_today = datetime.now().strftime("%Y-%m-%d")


def test_create_wellness(client, auth_headers):
    resp = client.post(
        "/api/wellness",
        json={
            "date": _today,
            "sleep_quality": 4,
            "fatigue": 2,
            "stress": 3,
            "soreness": 2,
            "mood": 4,
            "hrv": 55.3,
            "resting_hr": 58,
            "notes": "昨晚睡得不错",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["date"] == _today
    assert data["sleep_quality"] == 4
    assert data["hrv"] == 55.3


def test_upsert_wellness(client, auth_headers):
    # 第一次创建
    client.post("/api/wellness", json={"date": _today, "fatigue": 3}, headers=auth_headers)
    # 第二次更新
    resp = client.post("/api/wellness", json={"date": _today, "fatigue": 1}, headers=auth_headers)
    assert resp.status_code == 200

    # 验证只有一条记录
    resp = client.get("/api/wellness?days=1", headers=auth_headers)
    assert len(resp.get_json()["data"]) == 1
    assert resp.get_json()["data"][0]["fatigue"] == 1


def test_get_today(client, auth_headers):
    client.post("/api/wellness", json={"date": _today, "mood": 5}, headers=auth_headers)

    resp = client.get("/api/wellness/today", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data is not None
    assert data["mood"] == 5


def test_get_today_empty(client, auth_headers):
    from app.models.wellness import WellnessEntry

    # 确保今天的记录不存在
    user = _get_user(client, auth_headers)
    WellnessEntry.objects(user=user, date=_today).delete()

    resp = client.get("/api/wellness/today", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.get_json()["data"] is None


def test_list_wellness(client, auth_headers):
    client.post("/api/wellness", json={"date": _today, "sleep_quality": 3}, headers=auth_headers)

    resp = client.get("/api/wellness?days=7", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.get_json()["data"]) >= 1


def test_wellness_no_auth(client):
    resp = client.get("/api/wellness")
    assert resp.status_code == 401


def _get_user(client, auth_headers):
    from app.models.user import User

    token = auth_headers["Authorization"].replace("Bearer ", "")
    return User.objects(session_token=token).first()


def test_readiness_no_wellness(client, auth_headers):
    """无 wellness 记录时应返回纯训练负荷分。"""
    resp = client.get("/api/wellness/readiness", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["has_wellness_entry"] is False
    assert data["subjective_score"] == 0
    assert data["score"] >= 0


def test_readiness_with_wellness(client, auth_headers):
    """有 wellness 记录时主观分应 > 0。"""
    client.post(
        "/api/wellness",
        json={"date": _today, "sleep_quality": 5, "mood": 5, "fatigue": 1, "stress": 1, "soreness": 1},
        headers=auth_headers,
    )

    resp = client.get("/api/wellness/readiness", headers=auth_headers)
    data = resp.get_json()["data"]
    assert data["has_wellness_entry"] is True
    assert data["subjective_score"] > 0
    assert data["score"] >= 60  # 全部满分主观分 + 无训练 → 高分


def test_readiness_levels(client, auth_headers):
    """验证不同准备度等级。"""
    # 低主观分：高疲劳低睡眠 → 主观分很低
    client.post(
        "/api/wellness",
        json={"date": _today, "sleep_quality": 1, "fatigue": 5, "stress": 5, "soreness": 5, "mood": 1},
        headers=auth_headers,
    )
    resp = client.get("/api/wellness/readiness", headers=auth_headers)
    data = resp.get_json()["data"]
    # 即使主观分最低，无训练时 load_score=50，总分不会太低
    assert data["subjective_score"] < 15
    assert data["level"] in ("excellent", "good", "moderate", "low", "rest")


def test_missing_date(client, auth_headers):
    """缺少日期应返回 400。"""
    resp = client.post("/api/wellness", json={"sleep_quality": 3}, headers=auth_headers)
    assert resp.status_code == 400


def test_delete_wellness(client, auth_headers):
    """删除 wellness 记录。"""
    create = client.post("/api/wellness", json={"date": _today, "mood": 4}, headers=auth_headers)
    entry_id = create.get_json()["data"]["id"]

    resp = client.delete(f"/api/wellness/{entry_id}", headers=auth_headers)
    assert resp.status_code == 200

    resp = client.get("/api/wellness/today", headers=auth_headers)
    assert resp.get_json()["data"] is None


def test_delete_nonexistent(client, auth_headers):
    from bson import ObjectId

    resp = client.delete(f"/api/wellness/{ObjectId()}", headers=auth_headers)
    assert resp.status_code == 404


def test_weight_and_notes_roundtrip(client, auth_headers):
    """体重和备注字段正确保存和返回。"""
    client.post(
        "/api/wellness",
        json={"date": _today, "weight": 70.5, "notes": "感觉不错"},
        headers=auth_headers,
    )
    resp = client.get("/api/wellness?days=1", headers=auth_headers)
    entry = resp.get_json()["data"][0]
    assert entry["weight"] == 70.5
    assert entry["notes"] == "感觉不错"


def test_wellness_cross_user_isolation(client, app):
    """不同用户只能看到自己的数据。"""
    from app.models.user import User

    user_a = User(email="a@test.com", nickname="a")
    user_a.save()
    headers_a = {"Authorization": f"Bearer {user_a.generate_session_token()}"}

    user_b = User(email="b@test.com", nickname="b")
    user_b.save()
    headers_b = {"Authorization": f"Bearer {user_b.generate_session_token()}"}

    client.post("/api/wellness", json={"date": _today, "mood": 5}, headers=headers_a)

    resp = client.get("/api/wellness/today", headers=headers_b)
    assert resp.get_json()["data"] is None
