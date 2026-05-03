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


@pytest.fixture
def auth_token(app):
    """创建测试用户并返回认证 token。"""
    from app.models.user import User

    user = User(email="authtest@example.com", nickname="authtest")
    user.save()
    token = user.generate_session_token()
    return token


@pytest.fixture
def auth_headers(auth_token):
    """返回包含 Bearer token 的请求头。"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(autouse=True)
def _clean_db(app):
    """每个测试前后清理测试数据库中的数据。"""
    from app.models.activity import Activity
    from app.models.gear import Gear
    from app.models.user import User
    from app.models.verification_code import VerificationCode
    from app.models.athlete_settings import AthleteParams

    for col in (Activity, User, VerificationCode, AthleteParams, Gear):
        col.drop_collection()
    yield
    for col in (Activity, User, VerificationCode, AthleteParams, Gear):
        col.drop_collection()
