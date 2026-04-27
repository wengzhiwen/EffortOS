from datetime import datetime, timezone

from app.models.athlete_settings import AthleteParams


def test_hr_zones_with_lthr():
    params = AthleteParams(cycling_lthr=160, running_lthr=170)
    zones = params.get_hr_zones("cycling")
    assert len(zones) == 5
    assert zones[0]["name"] == "Z1"
    assert zones[4]["name"] == "Z5"
    # Z4 上限应约为 LTHR * 1.05 = 168
    assert 165 <= zones[3]["max"] <= 170


def test_hr_zones_running():
    params = AthleteParams(running_lthr=170)
    zones = params.get_hr_zones("running")
    assert len(zones) == 5


def test_hr_zones_fallback_to_max_hr():
    params = AthleteParams(max_heart_rate=190)
    zones = params.get_hr_zones("cycling")
    assert len(zones) == 5
    # LTHR 估算为 190 * 0.85 = 161


def test_hr_zones_no_data():
    params = AthleteParams()
    zones = params.get_hr_zones("cycling")
    assert zones == []


def test_power_zones():
    params = AthleteParams(ftp=250)
    zones = params.get_power_zones()
    assert len(zones) == 7
    assert zones[0]["name"] == "Z1"
    assert zones[6]["name"] == "Z7"
    # Z4 上限 = FTP * 1.05 = 262
    assert zones[3]["max"] == int(250 * 1.05)


def test_power_zones_no_ftp():
    params = AthleteParams()
    zones = params.get_power_zones()
    assert zones == []


def test_different_sport_lthr():
    """不同运动类型使用不同的 LTHR。"""
    params = AthleteParams(cycling_lthr=160, running_lthr=175, walking_lthr=140)
    cycling = params.get_hr_zones("cycling")
    running = params.get_hr_zones("running")
    walking = params.get_hr_zones("walking")

    # 不同 LTHR 应产生不同的分区
    assert cycling[2]["max"] != running[2]["max"]
    assert running[2]["max"] != walking[2]["max"]
