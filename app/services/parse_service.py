import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Optional


NS = {
    "tcx": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2",
    "ns3": "http://www.garmin.com/xmlschemas/ActivityExtension/v2",
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
