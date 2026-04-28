def test_app_creates(app):
    assert app is not None


def test_app_is_testing(app):
    assert app.config["TESTING"] is True


def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"EffortOS" in response.data


def test_landing_page_unauthenticated(client):
    """未登录用户首页显示落地页。"""
    response = client.get("/")
    assert response.status_code == 200
    assert b"EffortOS" in response.data


def test_settings_requires_login(client):
    """设置页未登录重定向。"""
    response = client.get("/settings")
    assert response.status_code == 302


def test_login_page_public(client):
    """登录页公开访问。"""
    response = client.get("/login")
    assert response.status_code == 200


def test_help_page_public(client):
    """帮助页公开访问。"""
    response = client.get("/help")
    assert response.status_code == 200
