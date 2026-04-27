import pytest


def test_create_params(client, auth_headers):
    resp = client.post(
        "/api/params",
        json={
            "effective_date": "2026-04-27",
            "ftp": 250,
            "cycling_lthr": 165,
            "running_lthr": 175,
            "max_heart_rate": 195,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["ftp"] == 250
    assert data["cycling_lthr"] == 165
    assert data["effective_date"] == "2026-04-27"


def test_create_params_no_auth(client):
    resp = client.post(
        "/api/params",
        json={"effective_date": "2026-04-27", "ftp": 200},
    )
    assert resp.status_code == 401


def test_create_params_missing_date(client, auth_headers):
    resp = client.post(
        "/api/params",
        json={"ftp": 200},
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_create_params_invalid_date(client, auth_headers):
    resp = client.post(
        "/api/params",
        json={"effective_date": "not-a-date", "ftp": 200},
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_get_latest_params_empty(client):
    resp = client.get("/api/params/latest")
    assert resp.status_code == 200
    assert resp.get_json()["data"] is None


def test_get_latest_params(client, auth_headers):
    client.post(
        "/api/params",
        json={"effective_date": "2026-04-27", "ftp": 250, "cycling_lthr": 165},
        headers=auth_headers,
    )

    resp = client.get("/api/params/latest")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["ftp"] == 250
    assert "hr_zones" in data
    assert "power_zones" in data


def test_get_params_history(client, auth_headers):
    client.post(
        "/api/params",
        json={"effective_date": "2026-04-20", "ftp": 200},
        headers=auth_headers,
    )
    client.post(
        "/api/params",
        json={"effective_date": "2026-04-27", "ftp": 250},
        headers=auth_headers,
    )

    resp = client.get("/api/params/history")
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert len(data) == 2
    # 按日期倒序
    assert data[0]["ftp"] == 250
    assert data[1]["ftp"] == 200
