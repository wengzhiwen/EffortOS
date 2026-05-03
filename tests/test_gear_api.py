import pytest


def test_create_gear(client, auth_headers):
    resp = client.post(
        "/api/gear",
        json={"name": "公路车", "gear_type": "bike", "distance_limit_km": 5000},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["name"] == "公路车"
    assert data["gear_type"] == "bike"
    assert data["total_distance_km"] == 0
    assert data["wear_percent"] == 0


def test_create_gear_missing_fields(client, auth_headers):
    resp = client.post("/api/gear", json={"name": "公路车"}, headers=auth_headers)
    assert resp.status_code == 400


def test_list_gear(client, auth_headers):
    client.post("/api/gear", json={"name": "公路车", "gear_type": "bike"}, headers=auth_headers)
    client.post("/api/gear", json={"name": "跑鞋", "gear_type": "shoes"}, headers=auth_headers)

    resp = client.get("/api/gear", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert len(data) == 2


def test_update_gear(client, auth_headers):
    create = client.post(
        "/api/gear",
        json={"name": "公路车", "gear_type": "bike"},
        headers=auth_headers,
    )
    gear_id = create.get_json()["data"]["id"]

    resp = client.put(
        f"/api/gear/{gear_id}",
        json={"name": "新公路车", "distance_limit_km": 8000},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["name"] == "新公路车"
    assert data["distance_limit_km"] == 8000


def test_delete_gear(client, auth_headers):
    create = client.post(
        "/api/gear",
        json={"name": "公路车", "gear_type": "bike"},
        headers=auth_headers,
    )
    gear_id = create.get_json()["data"]["id"]

    resp = client.delete(f"/api/gear/{gear_id}", headers=auth_headers)
    assert resp.status_code == 200

    resp = client.get("/api/gear", headers=auth_headers)
    assert len(resp.get_json()["data"]) == 0


def test_gear_no_auth(client):
    resp = client.get("/api/gear")
    assert resp.status_code == 401


def test_wear_percent(client, auth_headers):
    create = client.post(
        "/api/gear",
        json={"name": "跑鞋", "gear_type": "shoes", "distance_limit_km": 800},
        headers=auth_headers,
    )
    gear_id = create.get_json()["data"]["id"]

    # 模拟里程更新
    from app.models.gear import Gear

    gear = Gear.objects(id=gear_id).first()
    gear.total_distance_km = 400
    gear.save()

    resp = client.get("/api/gear", headers=auth_headers)
    data = resp.get_json()["data"]
    g = next(g for g in data if g["id"] == gear_id)
    assert g["wear_percent"] == 50.0
    assert not g["needs_replacement"]
