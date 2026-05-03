import os
import tempfile

import pytest

from app.services.parse_service import parse_activity_file, parse_gpx

# 带完整 trackpoint 数据的 GPX
GPX_WITH_TRACKPOINTS = """<?xml version="1.0" encoding="UTF-8"?>
<gpx creator="Test" version="1.1"
  xmlns="http://www.topografix.com/GPX/1/1"
  xmlns:ns3="http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <trk>
    <name>测试跑步</name>
    <type>running</type>
    <trkseg>
      <trkpt lat="39.9042" lon="116.4074">
        <ele>50.0</ele>
        <time>2026-04-27T08:00:00.000Z</time>
        <extensions>
          <ns3:TrackPointExtension>
            <ns3:hr>140</ns3:hr>
            <ns3:cadence>85</ns3:cadence>
          </ns3:TrackPointExtension>
        </extensions>
      </trkpt>
      <trkpt lat="39.9043" lon="116.4075">
        <ele>51.0</ele>
        <time>2026-04-27T08:00:01.000Z</time>
        <extensions>
          <ns3:TrackPointExtension>
            <ns3:hr>142</ns3:hr>
            <ns3:cadence>87</ns3:cadence>
          </ns3:TrackPointExtension>
        </extensions>
      </trkpt>
      <trkpt lat="39.9044" lon="116.4076">
        <ele>50.5</ele>
        <time>2026-04-27T08:00:02.000Z</time>
        <extensions>
          <ns3:TrackPointExtension>
            <ns3:hr>145</ns3:hr>
            <ns3:cadence>88</ns3:cadence>
          </ns3:TrackPointExtension>
        </extensions>
      </trkpt>
    </trkseg>
  </trk>
</gpx>"""

# 室内骑行空 track
GPX_INDOOR = """<?xml version="1.0" encoding="UTF-8"?>
<gpx creator="Garmin Connect" version="1.1"
  xmlns="http://www.topografix.com/GPX/1/1"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <metadata>
    <time>2026-04-27T06:34:45.000Z</time>
  </metadata>
  <trk>
    <name>室内骑行</name>
    <type>indoor_cycling</type>
    <trkseg/>
  </trk>
</gpx>"""


@pytest.fixture
def gpx_trackpoints_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".gpx", delete=False) as f:
        f.write(GPX_WITH_TRACKPOINTS)
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def gpx_indoor_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".gpx", delete=False) as f:
        f.write(GPX_INDOOR)
        path = f.name
    yield path
    os.unlink(path)


def test_parse_gpx_with_trackpoints(gpx_trackpoints_file):
    result = parse_gpx(gpx_trackpoints_file)

    assert result["sport"] == "running"
    assert len(result["trackpoints"]) == 3
    assert result["laps"] == []

    tp0 = result["trackpoints"][0]
    assert tp0["heart_rate"] == 140
    assert tp0["latitude"] == 39.9042
    assert tp0["longitude"] == 116.4074
    assert tp0["altitude"] == 50.0
    assert tp0["cadence"] == 85


def test_parse_gpx_indoor(gpx_indoor_file):
    result = parse_gpx(gpx_indoor_file)

    assert result["sport"] == "indoor_cycling"
    assert len(result["trackpoints"]) == 0
    assert result["start_time"] is not None


def test_parse_gpx_invalid_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".gpx", delete=False) as f:
        f.write("<root></root>")
        path = f.name
    try:
        with pytest.raises(ValueError, match="未找到 trk"):
            parse_gpx(path)
    finally:
        os.unlink(path)


def test_parse_activity_file_auto_detect():
    """测试 parse_activity_file 根据扩展名自动选择解析器。"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".gpx", delete=False) as f:
        f.write(GPX_INDOOR)
        gpx_path = f.name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".tcx", delete=False) as f:
        f.write("<root></root>")
        tcx_path = f.name
    try:
        result = parse_activity_file(gpx_path)
        assert result["sport"] == "indoor_cycling"

        with pytest.raises(ValueError):
            parse_activity_file(tcx_path)
    finally:
        os.unlink(gpx_path)
        os.unlink(tcx_path)


def test_parse_activity_file_unsupported():
    with pytest.raises(ValueError, match="不支持的文件格式"):
        parse_activity_file("test.fit")


def test_parse_real_gpx():
    """使用 samples 中的真实 GPX 文件测试。"""
    sample = "samples/activity_22674000886.gpx"
    if not os.path.exists(sample):
        pytest.skip("真实 GPX 样本文件不存在")

    result = parse_gpx(sample)
    assert result["sport"] == "indoor_cycling"
