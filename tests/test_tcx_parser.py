import os
import tempfile
import pytest

from app.services.parse_service import parse_tcx


# 最小化的 TCX 文件，包含一个 Lap 和三个 Trackpoint
MINIMAL_TCX = """<?xml version="1.0" encoding="UTF-8"?>
<TrainingCenterDatabase
  xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"
  xmlns:ns3="http://www.garmin.com/xmlschemas/ActivityExtension/v2"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <Activities>
    <Activity Sport="Biking">
      <Id>2026-04-27T06:34:45.000Z</Id>
      <Lap StartTime="2026-04-27T06:34:45.000Z">
        <TotalTimeSeconds>3.0</TotalTimeSeconds>
        <DistanceMeters>24.0</DistanceMeters>
        <MaximumSpeed>8.0</MaximumSpeed>
        <Calories>1</Calories>
        <AverageHeartRateBpm><Value>92</Value></AverageHeartRateBpm>
        <MaximumHeartRateBpm><Value>95</Value></MaximumHeartRateBpm>
        <Cadence>80</Cadence>
        <Track>
          <Trackpoint>
            <Time>2026-04-27T06:34:45.000Z</Time>
            <DistanceMeters>8.0</DistanceMeters>
            <HeartRateBpm><Value>90</Value></HeartRateBpm>
            <Cadence>78</Cadence>
            <Extensions>
              <ns3:TPX>
                <ns3:Speed>8.0</ns3:Speed>
                <ns3:Watts>100</ns3:Watts>
              </ns3:TPX>
            </Extensions>
          </Trackpoint>
          <Trackpoint>
            <Time>2026-04-27T06:34:46.000Z</Time>
            <DistanceMeters>16.0</DistanceMeters>
            <HeartRateBpm><Value>92</Value></HeartRateBpm>
            <Cadence>80</Cadence>
            <Extensions>
              <ns3:TPX>
                <ns3:Speed>8.0</ns3:Speed>
                <ns3:Watts>120</ns3:Watts>
              </ns3:TPX>
            </Extensions>
          </Trackpoint>
          <Trackpoint>
            <Time>2026-04-27T06:34:47.000Z</Time>
            <DistanceMeters>24.0</DistanceMeters>
            <HeartRateBpm><Value>95</Value></HeartRateBpm>
            <Cadence>82</Cadence>
            <Extensions>
              <ns3:TPX>
                <ns3:Speed>8.0</ns3:Speed>
                <ns3:Watts>110</ns3:Watts>
              </ns3:TPX>
            </Extensions>
          </Trackpoint>
        </Track>
      </Lap>
    </Activity>
  </Activities>
</TrainingCenterDatabase>"""


@pytest.fixture
def minimal_tcx_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".tcx", delete=False) as f:
        f.write(MINIMAL_TCX)
        path = f.name
    yield path
    os.unlink(path)


def test_parse_minimal_tcx(minimal_tcx_file):
    result = parse_tcx(minimal_tcx_file)

    assert result["sport"] == "cycling"
    assert len(result["trackpoints"]) == 3
    assert len(result["laps"]) == 1

    tp0 = result["trackpoints"][0]
    assert tp0["heart_rate"] == 90
    assert tp0["power"] == 100
    assert tp0["speed"] == 8.0
    assert tp0["cadence"] == 78
    assert tp0["distance"] == 8.0
    assert tp0["latitude"] is None  # 室内骑行无 GPS


def test_parse_tcx_lap_summary(minimal_tcx_file):
    result = parse_tcx(minimal_tcx_file)
    lap = result["laps"][0]

    assert lap["total_time_seconds"] == 3.0
    assert lap["distance_meters"] == 24.0
    assert lap["calories"] == 1
    assert lap["avg_heart_rate"] == 92
    assert lap["max_heart_rate"] == 95
    assert lap["cadence"] == 80


def test_parse_tcx_sport_mapping(minimal_tcx_file):
    """测试运动类型映射（直接修改 XML 太复杂，只验证已知映射）。"""
    result = parse_tcx(minimal_tcx_file)
    assert result["sport"] == "cycling"  # Biking -> cycling


def test_parse_tcx_invalid_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".tcx", delete=False) as f:
        f.write("<root></root>")
        path = f.name
    try:
        with pytest.raises(ValueError, match="未找到 Activity"):
            parse_tcx(path)
    finally:
        os.unlink(path)


def test_parse_real_tcx():
    """使用 samples 中的真实 TCX 文件测试。"""
    sample = "samples/activity_22674000886.tcx"
    if not os.path.exists(sample):
        pytest.skip("真实 TCX 样本文件不存在")

    result = parse_tcx(sample)
    assert result["sport"] == "cycling"
    assert len(result["trackpoints"]) > 100
    assert result["trackpoints"][0]["power"] is not None
