import io
import os
import tempfile

import pytest


MINIMAL_TCX = """<?xml version="1.0" encoding="UTF-8"?>
<TrainingCenterDatabase
  xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"
  xmlns:ns3="http://www.garmin.com/xmlschemas/ActivityExtension/v2"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <Activities>
    <Activity Sport="Biking">
      <Id>2026-04-27T06:34:45.000Z</Id>
      <Lap StartTime="2026-04-27T06:34:45.000Z">
        <TotalTimeSeconds>2.0</TotalTimeSeconds>
        <DistanceMeters>16.0</DistanceMeters>
        <Track>
          <Trackpoint>
            <Time>2026-04-27T06:34:45.000Z</Time>
            <DistanceMeters>8.0</DistanceMeters>
            <HeartRateBpm><Value>90</Value></HeartRateBpm>
            <Extensions>
              <ns3:TPX>
                <ns3:Speed>8.0</ns3:Speed>
                <ns3:Watts>100</ns3:Watts>
              </ns3:TPX>
            </Extensions>
          </Trackpoint>
          <Trackpoint>
            <Time>2026-04-27T06:34:47.000Z</Time>
            <DistanceMeters>16.0</DistanceMeters>
            <HeartRateBpm><Value>95</Value></HeartRateBpm>
            <Extensions>
              <ns3:TPX>
                <ns3:Speed>8.0</ns3:Speed>
                <ns3:Watts>120</ns3:Watts>
              </ns3:TPX>
            </Extensions>
          </Trackpoint>
        </Track>
      </Lap>
    </Activity>
  </Activities>
</TrainingCenterDatabase>"""


def test_upload_no_file(client):
    resp = client.post("/api/activities/upload")
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["code"] == 400
    assert "文件" in data["message"]


def test_upload_missing_activity_type(client):
    data = {
        "file": (io.BytesIO(MINIMAL_TCX.encode()), "test.tcx"),
    }
    resp = client.post("/api/activities/upload", data=data, content_type="multipart/form-data")
    assert resp.status_code == 400
    result = resp.get_json()
    assert "activity_type" in result["message"]


def test_upload_invalid_activity_type(client):
    data = {
        "file": (io.BytesIO(MINIMAL_TCX.encode()), "test.tcx"),
        "activity_type": "skydiving",
    }
    resp = client.post("/api/activities/upload", data=data, content_type="multipart/form-data")
    assert resp.status_code == 400
    result = resp.get_json()
    assert "不支持" in result["message"]


def test_upload_valid_tcx(client):
    data = {
        "file": (io.BytesIO(MINIMAL_TCX.encode()), "test.tcx"),
        "activity_type": "cycling",
        "name": "测试骑行",
    }
    resp = client.post("/api/activities/upload", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    result = resp.get_json()
    assert result["code"] == 200
    assert result["data"]["activity_type"] == "cycling"
    assert result["data"]["name"] == "测试骑行"
    assert result["data"]["trackpoint_count"] == 2
    assert result["data"]["data_summary"]["avg_heart_rate"] == 92
    assert result["data"]["data_summary"]["max_heart_rate"] == 95
    assert result["data"]["data_summary"]["avg_power"] == 110.0


def test_upload_invalid_file_content(client):
    data = {
        "file": (io.BytesIO(b"not xml content"), "test.tcx"),
        "activity_type": "cycling",
    }
    resp = client.post("/api/activities/upload", data=data, content_type="multipart/form-data")
    assert resp.status_code == 400
