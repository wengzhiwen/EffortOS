import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Optional


NS = {
    "tcx": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2",
    "ns3": "http://www.garmin.com/xmlschemas/ActivityExtension/v2",
}

GPX_NS = {
    "gpx": "http://www.topografix.com/GPX/1/1",
    "ns3": "http://www.garmin.com/xmlschemas/TrackPointExtension/v1",
}

GPX_SPORT_MAP = {
    "cycling": "cycling",
    "indoor_cycling": "indoor_cycling",
    "running": "running",
    "indoor_running": "indoor_running",
    "walking": "walking",
    "swimming": "swimming",
    "biking": "cycling",
    "ride": "cycling",
    "run": "running",
    "walk": "walking",
    "hiking": "walking",
}


def _parse_time(time_str: str) -> datetime:
    """解析 TCX 时间字符串为 UTC datetime。"""
    time_str = time_str.strip()
    if time_str.endswith("Z"):
        time_str = time_str[:-1] + "+00:00"
    return datetime.fromisoformat(time_str).astimezone(timezone.utc)


def _safe_float(element: ET.Element, path: str, namespaces: dict) -> Optional[float]:
    """安全地从 XML 元素提取浮点值。"""
    node = element.find(path, namespaces)
    if node is not None and node.text:
        return float(node.text)
    return None


def _safe_int(element: ET.Element, path: str, namespaces: dict) -> Optional[int]:
    """安全地从 XML 元素提取整数值。"""
    node = element.find(path, namespaces)
    if node is not None and node.text:
        return int(node.text)
    return None


def parse_tcx(file_path: str) -> dict:
    """解析 TCX 文件，返回运动数据字典。

    返回格式:
    {
        "sport": "cycling" | "running" | ...,
        "start_time": datetime,
        "trackpoints": [
            {
                "time": datetime,
                "heart_rate": int | None,
                "power": int | None,
                "speed": float | None,  # m/s
                "cadence": int | None,
                "distance": float | None,  # meters
                "latitude": float | None,
                "longitude": float | None,
                "altitude": float | None,
            },
            ...
        ],
        "laps": [
            {
                "start_time": datetime,
                "total_time_seconds": float,
                "distance_meters": float,
                "max_speed": float,
                "calories": int,
                "avg_heart_rate": int,
                "max_heart_rate": int,
                "cadence": int,
            },
            ...
        ],
    }
    """
    tree = ET.parse(file_path)
    root = tree.getroot()

    activity = root.find(".//tcx:Activity", NS)
    if activity is None:
        raise ValueError("TCX 文件中未找到 Activity 元素")

    # 解析运动类型
    sport_raw = activity.get("Sport", "").lower()
    sport_map = {
        "biking": "cycling",
        "running": "running",
        "walking": "walking",
        "swimming": "swimming",
        "other": "other",
    }
    sport = sport_map.get(sport_raw, "other")

    # 解析 Lap 汇总数据
    laps = []
    for lap in activity.findall("tcx:Lap", NS):
        lap_data = {
            "start_time": _parse_time(lap.get("StartTime")),
            "total_time_seconds": _safe_float(lap, "tcx:TotalTimeSeconds", NS),
            "distance_meters": _safe_float(lap, "tcx:DistanceMeters", NS),
            "max_speed": _safe_float(lap, "tcx:MaximumSpeed", NS),
            "calories": _safe_int(lap, "tcx:Calories", NS),
            "avg_heart_rate": _safe_int(lap, "tcx:AverageHeartRateBpm/tcx:Value", NS),
            "max_heart_rate": _safe_int(lap, "tcx:MaximumHeartRateBpm/tcx:Value", NS),
            "cadence": _safe_int(lap, "tcx:Cadence", NS),
        }
        laps.append(lap_data)

    # 解析 Trackpoint 时间序列
    trackpoints = []
    start_time = None
    for tp in activity.findall(".//tcx:Trackpoint", NS):
        time_val = tp.find("tcx:Time", NS)
        if time_val is None:
            continue
        time_dt = _parse_time(time_val.text)
        if start_time is None:
            start_time = time_dt

        # 位置
        lat = _safe_float(tp, "tcx:Position/tcx:LatitudeDegrees", NS)
        lon = _safe_float(tp, "tcx:Position/tcx:LongitudeDegrees", NS)
        alt = _safe_float(tp, "tcx:AltitudeMeters", NS)

        tp_data = {
            "time": time_dt,
            "heart_rate": _safe_int(tp, "tcx:HeartRateBpm/tcx:Value", NS),
            "power": _safe_int(tp, ".//ns3:Watts", NS),
            "speed": _safe_float(tp, ".//ns3:Speed", NS),
            "cadence": _safe_int(tp, "tcx:Cadence", NS),
            "distance": _safe_float(tp, "tcx:DistanceMeters", NS),
            "latitude": lat,
            "longitude": lon,
            "altitude": alt,
        }
        trackpoints.append(tp_data)

    if start_time is None:
        raise ValueError("TCX 文件中未找到有效的时间数据")

    return {
        "sport": sport,
        "start_time": start_time,
        "trackpoints": trackpoints,
        "laps": laps,
    }


def parse_gpx(file_path: str) -> dict:
    """解析 GPX 文件，返回运动数据字典。

    返回格式与 parse_tcx 一致（无 laps 字段）。
    """
    tree = ET.parse(file_path)
    root = tree.getroot()

    track = root.find(".//gpx:trk", GPX_NS)
    if track is None:
        raise ValueError("GPX 文件中未找到 trk 元素")

    # 运动类型：优先从 <type> 标签获取
    sport = "other"
    type_elem = track.find("gpx:type", GPX_NS)
    if type_elem is not None and type_elem.text:
        sport_raw = type_elem.text.strip().lower()
        sport = GPX_SPORT_MAP.get(sport_raw, "other")

    # 解析 trackpoint
    trackpoints = []
    start_time = None
    cumulative_distance = 0.0
    prev_tp = None

    for trkpt in track.findall(".//gpx:trkpt", GPX_NS):
        time_val = trkpt.find("gpx:time", GPX_NS)
        if time_val is None:
            continue
        time_dt = _parse_time(time_val.text)
        if start_time is None:
            start_time = time_dt

        # GPX 的 lat/lon 是 trkpt 元素的属性
        lat_attr = trkpt.get("lat")
        lon_attr = trkpt.get("lon")
        lat = float(lat_attr) if lat_attr else None
        lon = float(lon_attr) if lon_attr else None

        alt = _safe_float(trkpt, "gpx:ele", GPX_NS)

        # Garmin 扩展数据：心率、功率、踏频
        hr = _safe_int(trkpt, ".//ns3:hr", GPX_NS)
        power = _safe_int(trkpt, ".//ns3:power", GPX_NS)
        cadence = _safe_int(trkpt, ".//ns3:cadence", GPX_NS)

        # 距离：从扩展数据获取，或根据 GPS 坐标累加
        distance = _safe_float(trkpt, ".//ns3:DistanceMeters", GPX_NS)
        if distance is None and prev_tp and lat is not None and prev_tp.get("latitude") is not None:
            from math import sqrt, cos, radians

            dlat = lat - prev_tp["latitude"]
            dlon = (lon - prev_tp["longitude"]) * cos(radians(lat))
            cumulative_distance += sqrt(dlat ** 2 + (dlon * 111320) ** 2) * 111320
            distance = cumulative_distance

        # 速度：从扩展数据获取，或根据时间差和距离差推算
        speed = _safe_float(trkpt, ".//ns3:Speed", GPX_NS)

        tp_data = {
            "time": time_dt,
            "heart_rate": hr,
            "power": power,
            "speed": speed,
            "cadence": cadence,
            "distance": distance,
            "latitude": lat,
            "longitude": lon,
            "altitude": alt,
        }
        trackpoints.append(tp_data)
        prev_tp = tp_data

    # 如果没有 trackpoint，尝试从 metadata 获取时间
    if start_time is None:
        meta_time = root.find(".//gpx:metadata/gpx:time", GPX_NS)
        if meta_time is not None and meta_time.text:
            start_time = _parse_time(meta_time.text)

    if start_time is None:
        raise ValueError("GPX 文件中未找到有效的时间数据")

    return {
        "sport": sport,
        "start_time": start_time,
        "trackpoints": trackpoints,
        "laps": [],
    }


def parse_activity_file(file_path: str) -> dict:
    """根据文件扩展名自动选择解析器。"""
    if file_path.lower().endswith(".tcx"):
        return parse_tcx(file_path)
    elif file_path.lower().endswith(".gpx"):
        return parse_gpx(file_path)
    else:
        raise ValueError(f"不支持的文件格式: {file_path}")
