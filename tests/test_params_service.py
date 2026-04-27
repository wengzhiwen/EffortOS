from datetime import datetime, timezone

import pytest

from app.models.activity import Activity, DataSummary
from app.models.user import User
from app.services.params_service import (
    get_affected_activities,
    get_effective_params,
    mark_activities_for_recalc,
    save_params,
)


@pytest.fixture
def test_user(app):
    user = User(email="test@example.com", nickname="测试用户")
    user.save()
    yield user
    User.drop_collection()


def test_save_params_creates_new(test_user):
    params_data = {
        "effective_date": datetime(2026, 4, 1, tzinfo=timezone.utc),
        "ftp": 250,
        "max_heart_rate": 190,
    }
    params = save_params(test_user, params_data)
    assert params.ftp == 250
    assert params.max_heart_rate == 190


def test_save_params_no_change(test_user):
    params_data = {
        "effective_date": datetime(2026, 4, 1, tzinfo=timezone.utc),
        "ftp": 250,
    }
    first = save_params(test_user, params_data)
    second = save_params(test_user, params_data)

    # 无变更时返回同一条记录
    assert first.id == second.id


def test_save_params_with_change(test_user):
    params_data = {
        "effective_date": datetime(2026, 4, 1, tzinfo=timezone.utc),
        "ftp": 250,
    }
    first = save_params(test_user, params_data)

    # 变更 FTP
    params_data["ftp"] = 260
    second = save_params(test_user, params_data)

    assert first.id != second.id
    assert second.ftp == 260


def test_get_effective_params(test_user):
    # 两个不同日期的参数
    save_params(test_user, {
        "effective_date": datetime(2026, 3, 1, tzinfo=timezone.utc),
        "ftp": 240,
    })
    save_params(test_user, {
        "effective_date": datetime(2026, 4, 1, tzinfo=timezone.utc),
        "ftp": 250,
    })

    # 查询 3 月中旬的参数 → 应返回 3 月的
    params_march = get_effective_params(test_user, datetime(2026, 3, 15, tzinfo=timezone.utc))
    assert params_march.ftp == 240

    # 查询 4 月的参数 → 应返回 4 月的
    params_april = get_effective_params(test_user, datetime(2026, 4, 10, tzinfo=timezone.utc))
    assert params_april.ftp == 250


def test_get_affected_activities(test_user):
    Activity(
        user=test_user,
        activity_type="cycling",
        start_time=datetime(2026, 3, 15, tzinfo=timezone.utc),
        name="3月骑行",
    ).save()
    Activity(
        user=test_user,
        activity_type="cycling",
        start_time=datetime(2026, 4, 15, tzinfo=timezone.utc),
        name="4月骑行",
    ).save()

    affected = get_affected_activities(test_user, datetime(2026, 4, 1, tzinfo=timezone.utc))
    assert len(affected) == 1
    assert affected[0].name == "4月骑行"


def test_mark_activities_for_recalc(test_user):
    Activity(
        user=test_user,
        activity_type="cycling",
        start_time=datetime(2026, 4, 15, tzinfo=timezone.utc),
        name="需要重算",
        data_summary=DataSummary(duration_seconds=3600),
    ).save()
    Activity(
        user=test_user,
        activity_type="cycling",
        start_time=datetime(2026, 3, 15, tzinfo=timezone.utc),
        name="不需重算",
        data_summary=DataSummary(duration_seconds=3600),
    ).save()

    count = mark_activities_for_recalc(test_user, datetime(2026, 4, 1, tzinfo=timezone.utc))
    assert count == 1

    affected = Activity.objects(name="需要重算").first()
    assert affected.computed_metrics is None

    not_affected = Activity.objects(name="不需重算").first()
    assert not_affected.data_summary is not None
