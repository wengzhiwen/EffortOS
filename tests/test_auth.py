import json


def test_request_code(client):
    resp = client.post("/api/auth/request-code",
                       data=json.dumps({"email": "test@example.com"}),
                       content_type="application/json")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["code"] == 200
    # 开发环境应返回验证码
    assert data["data"]["code"] is not None


def test_request_code_invalid_email(client):
    resp = client.post("/api/auth/request-code",
                       data=json.dumps({"email": "invalid"}),
                       content_type="application/json")
    assert resp.status_code == 400


def test_verify_and_login(client):
    # 先请求验证码
    resp = client.post("/api/auth/request-code",
                       data=json.dumps({"email": "test@example.com"}),
                       content_type="application/json")
    code = resp.get_json()["data"]["code"]

    # 验证登录
    resp = client.post("/api/auth/verify",
                       data=json.dumps({"email": "test@example.com", "code": code}),
                       content_type="application/json")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["data"]["token"] is not None
    assert data["data"]["user"]["email"] == "test@example.com"


def test_verify_wrong_code(client):
    client.post("/api/auth/request-code",
                data=json.dumps({"email": "test@example.com"}),
                content_type="application/json")

    resp = client.post("/api/auth/verify",
                       data=json.dumps({"email": "test@example.com", "code": "000000"}),
                       content_type="application/json")
    assert resp.status_code == 400


def test_me_authenticated(client):
    # 登录
    resp = client.post("/api/auth/request-code",
                       data=json.dumps({"email": "test@example.com"}),
                       content_type="application/json")
    code = resp.get_json()["data"]["code"]

    resp = client.post("/api/auth/verify",
                       data=json.dumps({"email": "test@example.com", "code": code}),
                       content_type="application/json")
    token = resp.get_json()["data"]["token"]

    # 查看当前用户
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.get_json()["data"]["email"] == "test@example.com"


def test_me_unauthenticated(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_logout(client):
    # 先登录
    resp = client.post("/api/auth/request-code",
                       data=json.dumps({"email": "test@example.com"}),
                       content_type="application/json")
    code = resp.get_json()["data"]["code"]

    resp = client.post("/api/auth/verify",
                       data=json.dumps({"email": "test@example.com", "code": code}),
                       content_type="application/json")
    token = resp.get_json()["data"]["token"]

    # 登出
    resp = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    # 验证 token 已失效
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
