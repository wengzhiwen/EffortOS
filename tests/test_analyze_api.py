import io

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


def test_analyze_no_auth(client):
    resp = client.post("/api/activities/analyze")
    assert resp.status_code == 401


def test_analyze_no_file(client, auth_headers):
    resp = client.post("/api/activities/analyze", headers=auth_headers)
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["code"] == 400


def test_analyze_invalid_ext(client, auth_headers):
    data = {
        "file": (io.BytesIO(b"content"), "test.txt"),
    }
    resp = client.post("/api/activities/analyze", data=data, headers=auth_headers, content_type="multipart/form-data")
    assert resp.status_code == 400
    result = resp.get_json()
    assert "格式" in result["message"]


def test_analyze_invalid_content(client, auth_headers):
    data = {
        "file": (io.BytesIO(b"not xml"), "test.tcx"),
    }
    resp = client.post("/api/activities/analyze", data=data, headers=auth_headers, content_type="multipart/form-data")
    assert resp.status_code == 400


def test_analyze_valid_tcx(client, auth_headers):
    data = {
        "file": (io.BytesIO(MINIMAL_TCX.encode()), "test.tcx"),
    }
    resp = client.post("/api/activities/analyze", data=data, headers=auth_headers, content_type="multipart/form-data")
    assert resp.status_code == 200
    result = resp.get_json()
    assert result["code"] == 200
    d = result["data"]
    assert d["sport"] == "cycling"
    assert d["sport_display"] == "骑行"
    assert "骑行" in d["name_suggestion"]
    assert d["duration_seconds"] == 2
    assert d["total_distance"] == 16.0
    assert d["trackpoint_count"] == 2
    assert d["has_heart_rate"] is True
    assert d["has_power"] is True
    assert isinstance(d["warnings"], list)


def test_analyze_no_heart_rate(client, auth_headers):
    no_hr_tcx = MINIMAL_TCX.replace("<HeartRateBpm><Value>90</Value></HeartRateBpm>", "")
    no_hr_tcx = no_hr_tcx.replace("<HeartRateBpm><Value>95</Value></HeartRateBpm>", "")
    data = {
        "file": (io.BytesIO(no_hr_tcx.encode()), "test.tcx"),
    }
    resp = client.post("/api/activities/analyze", data=data, headers=auth_headers, content_type="multipart/form-data")
    assert resp.status_code == 200
    result = resp.get_json()
    d = result["data"]
    assert d["has_heart_rate"] is False
    assert any("心率" in w for w in d["warnings"])


def test_analyze_temp_file_cleaned(client, auth_headers):
    """验证临时文件被清理（不会累积在 upload 目录）。"""
    import os

    upload_dir = client.application.config["UPLOAD_FOLDER"]
    before = set(os.listdir(upload_dir)) if os.path.exists(upload_dir) else set()
    data = {
        "file": (io.BytesIO(MINIMAL_TCX.encode()), "test.tcx"),
    }
    client.post("/api/activities/analyze", data=data, headers=auth_headers, content_type="multipart/form-data")
    after = set(os.listdir(upload_dir)) if os.path.exists(upload_dir) else set()
    new_files = after - before
    assert all(not f.startswith("_analyze_") for f in new_files), f"临时文件未清理: {new_files}"
