import pytest

from app import create_app


@pytest.fixture
def app():
    app = create_app("testing")
    yield app

    # 清理测试数据库
    from mongoengine import disconnect

    disconnect(alias="default")


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def _clean_db(app):
    """每个测试前后清理测试数据库中的数据。"""
    from app.models.activity import Activity

    Activity.drop_collection()
    yield
    Activity.drop_collection()
