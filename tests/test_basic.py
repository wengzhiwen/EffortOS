def test_app_creates(app):
    assert app is not None


def test_app_is_testing(app):
    assert app.config["TESTING"] is True


def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"EffortOS" in response.data


def test_about_page(client):
    response = client.get("/about")
    assert response.status_code == 200
