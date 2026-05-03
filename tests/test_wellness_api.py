from datetime import datetime

import pytest


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
