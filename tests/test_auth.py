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


def _login(client):
    """辅助：登录并返回 token。"""
    resp = client.post("/api/auth/request-code",
                       data=json.dumps({"email": "test@example.com"}),
                       content_type="application/json")
    code = resp.get_json()["data"]["code"]
    resp = client.post("/api/auth/verify",
                       data=json.dumps({"email": "test@example.com", "code": code}),
                       content_type="application/json")
    return resp.get_json()["data"]["token"]


def test_update_profile(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.put("/api/auth/profile",
                      data=json.dumps({"nickname": "新昵称"}),
                      content_type="application/json",
                      headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["data"]["nickname"] == "新昵称"

    # 验证已更新
    resp = client.get("/api/auth/me", headers=headers)
    assert resp.get_json()["data"]["nickname"] == "新昵称"


def test_update_profile_empty_nickname(client):
    token = _login(client)
    resp = client.put("/api/auth/profile",
                      data=json.dumps({"nickname": ""}),
                      content_type="application/json",
                      headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400


def test_request_code_missing_email(client):
    resp = client.post("/api/auth/request-code",
                       data=json.dumps({}),
                       content_type="application/json")
    assert resp.status_code == 400


def test_verify_missing_fields(client):
    resp = client.post("/api/auth/verify",
                       data=json.dumps({}),
                       content_type="application/json")
    assert resp.status_code == 400


def test_update_profile_no_auth(client):
    resp = client.put("/api/auth/profile",
                      data=json.dumps({"nickname": "hacker"}),
                      content_type="application/json")
    assert resp.status_code == 401


def test_logout_no_auth(client):
    """未登录登出也应成功（幂等）。"""
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 200


def test_invalid_token(client):
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid-token"})
    assert resp.status_code == 401
