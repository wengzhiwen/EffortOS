import csv
import io
import os
import re
import shutil
import time
import uuid

from flask import Blueprint, Response, current_app, jsonify, request

from app.models.activity import Activity, DataSummary, Trackpoint
from app.services.parse_service import parse_activity_file
from app.services.validate_service import compute_file_checksum, validate_activity_file
from app.utils.auth import get_authenticated_user, require_user, user_filter

activities_bp = Blueprint("activities", __name__)

VALID_ACTIVITY_TYPES = [
    "cycling",
    "indoor_cycling",
    "commute_cycling",
    "running",
    "indoor_running",
    "walking",
    "swimming",
    "other",
]

SPORT_DISPLAY = {
    "cycling": "骑行",
    "indoor_cycling": "室内骑行",
    "commute_cycling": "通勤骑行",
    "running": "跑步",
    "indoor_running": "室内跑步",
    "walking": "步行",
    "swimming": "游泳",
    "other": "其他",
}

# 室内/室外配对关系
INDOOR_PAIRS = {
    "cycling": "indoor_cycling",
    "running": "indoor_running",
    "indoor_cycling": "cycling",
    "indoor_running": "running",
}


def _user_filter(qs):
    """按当前用户过滤查询集（无用户时返回全集）。"""
    return user_filter(qs)


def _suggest_activity_type(activity):
    """基于 Trackpoint 中的 GPS 数据判断运动类型是否可能有误，返回建议类型。

    判断逻辑与 parse_service.detect_indoor_activity 一致：
    1. 当前是室外，但 GPS 覆盖率极低或 GPS 累计移动距离极短 → 建议室内
    2. 当前是室内，但 GPS 覆盖率高且 GPS 累计移动距离显著 → 建议室外
    """
    from math import cos, radians, sqrt

    current = activity.activity_type
    pair = INDOOR_PAIRS.get(current)
    if not pair:
        return None

    tps = activity.trackpoints
    if not tps or len(tps) < 2:
        return None

    duration = tps[-1].elapsed - tps[0].elapsed
    if duration < 120:
        return None

    gps_points = [tp for tp in tps if tp.latitude is not None and tp.longitude is not None]
    gps_ratio = len(gps_points) / len(tps)
    has_gps = gps_ratio >= 0.1

    # 计算 GPS 累计移动距离
    gps_distance = 0.0
    if has_gps and len(gps_points) >= 2:
        prev = gps_points[0]
        for tp in gps_points[1:]:
            dlat = tp.latitude - prev.latitude
            dlon = (tp.longitude - prev.longitude) * cos(radians(tp.latitude))
            gps_distance += sqrt((dlat * 111320) ** 2 + (dlon * 111320) ** 2)
            prev = tp

    is_outdoor = current in ("cycling", "running")

    if is_outdoor:
        # 室外但没 GPS 或 GPS 几乎没动 → 建议室内
        if not has_gps:
            return pair
        avg_gps_speed = gps_distance / duration
        if current == "cycling" and (avg_gps_speed < 0.56 or gps_distance < 200):
            return "indoor_cycling"
        if current == "running" and (avg_gps_speed < 0.28 or gps_distance < 100):
            return "indoor_running"
    else:
        # 室内但有可靠 GPS 且 GPS 移动显著 → 建议室外
        base = current.replace("indoor_", "")
        if has_gps:
            avg_gps_speed = gps_distance / duration
            if base == "cycling" and avg_gps_speed > 3 and gps_distance > 1000:
                return "cycling"
            if base == "running" and avg_gps_speed > 1.5 and gps_distance > 500:
                return "running"

    return None


def _activity_type_filter(qs):
    """按请求参数过滤运动类型。"""
    activity_type = request.args.get("activity_type")
    return qs.filter(activity_type=activity_type) if activity_type else qs


def _end_of_day(date_str):
    """将 'YYYY-MM-DD' 转为当天 23:59:59 的 datetime 对象（用于 __lte 查询）。"""
    from datetime import datetime

    return datetime.strptime(date_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59)


def _date_range_filter(qs):
    """按请求参数过滤日期范围。"""
    start_date = request.args.get("start_date")
    if start_date:
        qs = qs.filter(start_time__gte=start_date)
    end_date = request.args.get("end_date")
    if end_date:
        qs = qs.filter(start_time__lte=_end_of_day(end_date))
    return qs


def _intensity_level_filter(qs):
    """按请求参数过滤强度等级。"""
    level = request.args.get("intensity_level")
    if level:
        qs = qs.filter(computed_metrics__intensity_level=level)
    return qs


def _name_filter(qs):
    """按名称关键词搜索。"""
    keyword = request.args.get("search", "").strip()
    if keyword:
        qs = qs.filter(name__icontains=keyword)
    return qs


# ============================================================
# 序列化辅助
# ============================================================


def _serialize_summary(summary):
    """将 DataSummary 序列化为字典。"""
    if not summary:
        return None
    return {
        "duration_seconds": summary.duration_seconds,
        "total_distance": summary.total_distance,
        "avg_heart_rate": summary.avg_heart_rate,
        "max_heart_rate": summary.max_heart_rate,
        "avg_power": round(summary.avg_power, 1) if summary.avg_power else None,
        "max_power": summary.max_power,
        "avg_speed": round(summary.avg_speed, 2) if summary.avg_speed else None,
        "max_speed": round(summary.max_speed, 2) if summary.max_speed else None,
        "avg_cadence": summary.avg_cadence,
        "max_cadence": summary.max_cadence,
        "elevation_gain": summary.elevation_gain,
        "elevation_loss": summary.elevation_loss,
    }


def _serialize_activity(activity):
    """将 Activity 序列化为字典。"""
    return {
        "id": str(activity.id),
        "activity_type": activity.activity_type,
        "name": activity.name or "",
        "start_time": activity.start_time.isoformat(),
        "source_format": activity.source_format,
        "notes": activity.notes or "",
        "data_summary": _serialize_summary(activity.data_summary),
        "computed_metrics": _serialize_metrics(activity.computed_metrics),
        "created_at": activity.created_at.isoformat() if activity.created_at else None,
    }


def _serialize_metrics(metrics):
    """将 ComputedMetrics 序列化为字典。"""
    if not metrics:
        return None
    has_any = metrics.tss is not None or metrics.hr_tss is not None or metrics.manual_tss is not None
    if not has_any and not metrics.normalized_power and not metrics.intensity_level:
        return None
    return {
        "tss": metrics.tss,
        "tss_method": metrics.tss_method,
        "hr_tss": metrics.hr_tss,
        "manual_tss": metrics.manual_tss,
        "intensity_factor": metrics.intensity_factor,
        "hr_intensity_factor": metrics.hr_intensity_factor,
        "normalized_power": metrics.normalized_power,
        "variability_index": metrics.variability_index,
        "efficiency_factor": metrics.efficiency_factor,
        "work_kj": metrics.work_kj,
        "intensity_level": metrics.intensity_level,
        "intensity_reason": metrics.intensity_reason,
        "hr_zones_time": metrics.hr_zones_time,
        "power_zones_time": metrics.power_zones_time,
        "best_efforts": metrics.best_efforts,
    }


# ============================================================
# 内部计算辅助
# ============================================================


def _calc_pb_markers(activities, full_qs):
    """计算每个活动哪些窗口是当前全局最佳（PB）。

    PB 仅基于功率指标。只有各窗口的当前记录保持者才标记 PB。
    如果新活动刷新了 PB，旧活动的 PB 标记会自动消失。

    返回 {activity_id: ["5", "60", ...]} — 列表中是达到全局最佳的窗口秒数字符串。
    """
    if not activities:
        return {}

    # 先找出所有活动在各窗口的全局最佳值
    global_best = {}  # {"5": 300.0, "60": 250.0, ...}
    all_activities = list(full_qs.only("computed_metrics"))
    for a in all_activities:
        cm = a.computed_metrics
        if not cm or not cm.best_efforts:
            continue
        for window, val in cm.best_efforts.get("power", {}).items():
            if val is not None and (window not in global_best or val > global_best[window]):
                global_best[window] = val

    # 标记当前页中达到全局最佳的活动
    pb_map = {}
    for a in activities:
        aid = str(a.id)
        cm = a.computed_metrics
        pb_windows = []
        if cm and cm.best_efforts:
            for window, val in cm.best_efforts.get("power", {}).items():
                if val is not None and val == global_best.get(window):
                    pb_windows.append(window)
        pb_map[aid] = pb_windows

    return pb_map


def _build_data_summary(laps, trackpoints):
    """从解析数据构建 DataSummary。"""
    summary = DataSummary()

    if not trackpoints:
        return summary

    # 运动时长：相邻打点间隔 ≤30s 的累计（排除暂停）
    active = 0.0
    for i in range(1, len(trackpoints)):
        dt = (trackpoints[i]["time"] - trackpoints[i - 1]["time"]).total_seconds()
        if dt <= 30:
            active += dt
    summary.duration_seconds = (
        int(active) if active > 0 else int((trackpoints[-1]["time"] - trackpoints[0]["time"]).total_seconds())
    )

    distances = [tp["distance"] for tp in trackpoints if tp.get("distance") is not None]
    if distances:
        summary.total_distance = distances[-1]

    hrs = [tp["heart_rate"] for tp in trackpoints if tp.get("heart_rate") is not None]
    if hrs:
        summary.avg_heart_rate = sum(hrs) // len(hrs)
        summary.max_heart_rate = max(hrs)

    powers = [tp["power"] for tp in trackpoints if tp.get("power") is not None]
    if powers:
        summary.avg_power = sum(powers) / len(powers)
        summary.max_power = max(powers)

    speeds = [tp["speed"] for tp in trackpoints if tp.get("speed") is not None]
    if speeds:
        summary.avg_speed = sum(speeds) / len(speeds)
        summary.max_speed = max(speeds)

    cadences = [tp["cadence"] for tp in trackpoints if tp.get("cadence") is not None]
    if cadences:
        summary.avg_cadence = sum(cadences) // len(cadences)
        summary.max_cadence = max(cadences)

    return summary


def _compute_metrics(activity, trackpoints):
    """计算并填充 Activity 的 ComputedMetrics。"""
    from app.services.metrics_service import compute_activity_metrics
    from app.services.params_service import get_effective_params
    from app.utils.auth import get_authenticated_user

    current_user = get_authenticated_user()
    if not trackpoints:
        return

    # 使用活动日期对应的参数
    params = get_effective_params(current_user, activity.start_time)
    if not params:
        return

    activity_type = activity.activity_type
    hr_zones = params.get_hr_zones(activity_type)
    power_zones = params.get_power_zones() if activity_type in ("cycling", "indoor_cycling", "commute_cycling") else []

    lthr_map = {
        "cycling": params.cycling_lthr,
        "indoor_cycling": params.cycling_lthr,
        "commute_cycling": params.cycling_lthr,
        "running": params.running_lthr,
        "indoor_running": params.running_lthr,
        "walking": params.walking_lthr,
    }
    lthr = lthr_map.get(activity_type)

    activity.computed_metrics = compute_activity_metrics(
        trackpoints=trackpoints,
        activity_type=activity_type,
        hr_zones=hr_zones,
        power_zones=power_zones,
        ftp=params.ftp,
        lthr=lthr,
    )


# ============================================================
# 端点
# ============================================================


def _analyze_trackpoints(trackpoints, sport):
    """分析轨迹点数据，返回预览信息（时长、距离、数据质量、警告等）。"""
    total = len(trackpoints)
    start = trackpoints[0]["time"] if trackpoints else None

    hr_count = sum(1 for tp in trackpoints if tp.get("heart_rate") is not None)
    power_count = sum(1 for tp in trackpoints if tp.get("power") is not None)
    speed_count = sum(1 for tp in trackpoints if tp.get("speed") is not None)
    dist_count = sum(1 for tp in trackpoints if tp.get("distance") is not None)

    # GPS 分析
    gps_count = sum(1 for tp in trackpoints if tp.get("latitude") is not None and tp.get("longitude") is not None)
    has_gps = total > 0 and gps_count / total >= 0.1
    gps_tag = None
    if has_gps and sport in ("cycling", "running") and total >= 2:
        from math import cos, radians, sqrt

        duration_sec = (trackpoints[-1]["time"] - trackpoints[0]["time"]).total_seconds()
        if duration_sec >= 120:
            gps_points = [
                tp for tp in trackpoints if tp.get("latitude") is not None and tp.get("longitude") is not None
            ]
            gps_dist = 0.0
            prev = gps_points[0]
            for tp in gps_points[1:]:
                dlat = tp["latitude"] - prev["latitude"]
                dlon = (tp["longitude"] - prev["longitude"]) * cos(radians(tp["latitude"]))
                gps_dist += sqrt((dlat * 111320) ** 2 + (dlon * 111320) ** 2)
                prev = tp
            avg_gps_speed = gps_dist / duration_sec
            if (
                sport == "cycling"
                and (avg_gps_speed < 0.56 or gps_dist < 200)
                or sport == "running"
                and (avg_gps_speed < 0.28 or gps_dist < 100)
            ):
                gps_tag = "low_quality"

    warnings = []
    if total == 0:
        warnings.append("文件中没有轨迹数据点")
    else:
        hr_pct = hr_count / total
        power_pct = power_count / total
        if hr_pct < 0.1:
            warnings.append("心率数据缺失超过 90%，无法计算心率相关指标")
        if sport in ("cycling", "indoor_cycling") and power_pct < 0.1:
            warnings.append("功率数据缺失，将使用心率计算 TSS")
        if dist_count == 0 and speed_count == 0:
            warnings.append("无距离和速度数据")
        if gps_tag == "low_quality":
            warnings.append("GPS 移动距离极短，疑似室内活动（GPS 飘星）")

    # 基础摘要
    duration = 0
    total_dist = 0
    avg_hr = 0
    if trackpoints:
        active = 0.0
        for i in range(1, len(trackpoints)):
            dt = (trackpoints[i]["time"] - trackpoints[i - 1]["time"]).total_seconds()
            if dt <= 30:
                active += dt
        duration = (
            int(active) if active > 0 else int((trackpoints[-1]["time"] - trackpoints[0]["time"]).total_seconds())
        )
        distances = [tp["distance"] for tp in trackpoints if tp.get("distance") is not None]
        if distances:
            total_dist = distances[-1]
        hrs = [tp["heart_rate"] for tp in trackpoints if tp.get("heart_rate") is not None]
        if hrs:
            avg_hr = sum(hrs) // len(hrs)

    name_suggestion = f"{start.strftime('%m月%d日')}{SPORT_DISPLAY.get(sport, sport)}" if start else "未知活动"

    return {
        "sport": sport,
        "sport_display": SPORT_DISPLAY.get(sport, sport),
        "name_suggestion": name_suggestion,
        "start_time": start.isoformat() if start else None,
        "duration_seconds": duration,
        "total_distance": round(total_dist, 1),
        "avg_heart_rate": avg_hr,
        "trackpoint_count": total,
        "has_heart_rate": hr_count > total * 0.5,
        "has_power": power_count > total * 0.5,
        "has_gps": has_gps,
        "gps_tag": gps_tag,
        "warnings": warnings,
    }


def _cleanup_expired_batch_sessions(upload_dir, max_age_seconds=3600):
    """清理过期的批量上传会话目录。"""
    batch_dir = os.path.join(upload_dir, "_batch")
    if not os.path.isdir(batch_dir):
        return
    now = time.time()
    for name in os.listdir(batch_dir):
        path = os.path.join(batch_dir, name)
        if os.path.isdir(path) and now - os.path.getmtime(path) > max_age_seconds:
            shutil.rmtree(path, ignore_errors=True)


@activities_bp.route("/activities/analyze", methods=["POST"])
def analyze_activity():
    """预分析运动数据文件，返回运动类型、名称建议和数据质量。"""
    user, err = require_user()
    if err:
        return err

    if "file" not in request.files:
        return jsonify({"code": 400, "message": "未找到文件", "data": None}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"code": 400, "message": "文件名为空", "data": None}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("tcx", "gpx"):
        return jsonify({"code": 400, "message": f"不支持的文件格式: .{ext}", "data": None}), 400

    # 临时保存文件用于解析
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    tmp_path = os.path.join(upload_dir, f"_analyze_{uuid.uuid4().hex}.{ext}")
    file.save(tmp_path)

    try:
        is_valid, error_msg = validate_activity_file(tmp_path)
        if not is_valid:
            return jsonify({"code": 400, "message": error_msg, "data": None}), 400
        parsed = parse_activity_file(tmp_path)
    except ValueError as e:
        return jsonify({"code": 422, "message": f"文件解析失败: {str(e)}", "data": None}), 422

    trackpoints = parsed["trackpoints"]
    sport = parsed.get("sport", "other")
    checksum = compute_file_checksum(tmp_path)

    # 检查重复
    existing = Activity.objects(user=user, file_checksum=checksum).first()
    is_duplicate = existing is not None

    # 清理临时文件
    if os.path.exists(tmp_path):
        os.remove(tmp_path)

    preview = _analyze_trackpoints(trackpoints, sport)
    preview["checksum"] = checksum
    preview["is_duplicate"] = is_duplicate

    return jsonify({"code": 200, "message": "ok", "data": preview})


@activities_bp.route("/activities/upload", methods=["POST"])
def upload_activity():
    """上传运动数据文件（TCX/GPX）。"""
    user, err = require_user()
    if err:
        return err

    if "file" not in request.files:
        return jsonify({"code": 400, "message": "未找到上传文件", "data": None}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"code": 400, "message": "文件名为空", "data": None}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ("tcx", "gpx"):
        return jsonify({"code": 400, "message": f"不支持的文件格式: .{ext}", "data": None}), 400

    activity_type = request.form.get("activity_type", "").strip()
    if not activity_type:
        return jsonify({"code": 400, "message": "缺少 activity_type 参数", "data": None}), 400
    if activity_type not in VALID_ACTIVITY_TYPES:
        return jsonify({"code": 400, "message": f"不支持的运动类型: {activity_type}", "data": None}), 400

    # 保存文件到 upload 目录
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    safe_filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(upload_dir, safe_filename)
    file.save(file_path)

    # 校验 + 解析
    is_valid, error_msg = validate_activity_file(file_path)
    if not is_valid:
        os.remove(file_path)
        return jsonify({"code": 400, "message": error_msg, "data": None}), 400

    try:
        parsed = parse_activity_file(file_path)
    except ValueError as e:
        os.remove(file_path)
        return jsonify({"code": 422, "message": f"文件解析失败: {str(e)}", "data": None}), 422

    # 文件校验和去重
    checksum = compute_file_checksum(file_path)
    if Activity.objects(user=user, file_checksum=checksum).first():
        os.remove(file_path)
        return jsonify({"code": 409, "message": "该文件已上传过", "data": None}), 409

    trackpoints = parsed["trackpoints"]
    data_summary = _build_data_summary(parsed["laps"], trackpoints)
    name = request.form.get("name") or file.filename

    activity = Activity(
        activity_type=activity_type,
        name=name,
        start_time=parsed["start_time"],
        source_file=safe_filename,
        source_format=ext,
        file_checksum=checksum,
        data_summary=data_summary,
        raw_data_path=file_path,
        user=user,
    )

    if trackpoints:
        first_time = trackpoints[0]["time"]
        activity.trackpoints = [
            Trackpoint(
                elapsed=(tp["time"] - first_time).total_seconds(),
                hr=tp.get("heart_rate"),
                power=tp.get("power"),
                speed=tp.get("speed"),
                cadence=tp.get("cadence"),
                altitude=tp.get("altitude"),
                distance=tp.get("distance"),
                latitude=tp.get("latitude"),
                longitude=tp.get("longitude"),
            )
            for tp in trackpoints
        ]

    _compute_metrics(activity, parsed["trackpoints"])
    activity.save()

    return jsonify(
        {
            "code": 200,
            "message": "上传成功",
            "data": {
                "id": str(activity.id),
                "activity_type": activity.activity_type,
                "name": activity.name or "",
                "start_time": activity.start_time.isoformat(),
                "data_summary": _serialize_summary(data_summary),
                "computed_metrics": _serialize_metrics(activity.computed_metrics),
                "trackpoint_count": len(trackpoints),
            },
        }
    )


@activities_bp.route("/activities/batch-analyze", methods=["POST"])
def batch_analyze():
    """批量预分析多个运动数据文件，返回分析结果列表（按时间排序）。"""
    user, err = require_user()
    if err:
        return err

    files = request.files.getlist("files")
    if not files:
        return jsonify({"code": 400, "message": "未找到文件", "data": None}), 400
    if len(files) > 30:
        return jsonify({"code": 400, "message": "单次最多 30 个文件", "data": None}), 400

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)

    # 清理过期会话
    _cleanup_expired_batch_sessions(upload_dir)

    # 创建本次会话目录
    session_id = uuid.uuid4().hex
    session_dir = os.path.join(upload_dir, "_batch", session_id)
    os.makedirs(session_dir, exist_ok=True)

    results = []
    for file in files:
        if not file.filename:
            continue
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in ("tcx", "gpx"):
            results.append({"filename": file.filename, "error": f"不支持的格式: .{ext}"})
            continue

        safe_name = f"{uuid.uuid4().hex}.{ext}"
        tmp_path = os.path.join(session_dir, safe_name)
        file.save(tmp_path)

        try:
            is_valid, error_msg = validate_activity_file(tmp_path)
            if not is_valid:
                results.append({"filename": file.filename, "error": error_msg})
                os.remove(tmp_path)
                continue

            parsed = parse_activity_file(tmp_path)
            checksum = compute_file_checksum(tmp_path)

            # 去重检查
            existing = Activity.objects(user=user, file_checksum=checksum).first()
            is_dup = existing is not None

            trackpoints = parsed["trackpoints"]
            sport = parsed.get("sport", "other")
            preview = _analyze_trackpoints(trackpoints, sport)

            results.append(
                {
                    "temp_id": safe_name,
                    "filename": file.filename,
                    "checksum": checksum,
                    "is_duplicate": is_dup,
                    **preview,
                }
            )
        except ValueError as e:
            results.append({"filename": file.filename, "error": f"解析失败: {str(e)}"})
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    # 按时间排序：有效结果在前，错误在后
    valid = [r for r in results if "error" not in r]
    valid.sort(key=lambda r: r.get("start_time") or "")
    errors = [r for r in results if "error" in r]

    return jsonify({"code": 200, "message": "ok", "data": {"session_id": session_id, "items": valid + errors}})


@activities_bp.route("/activities/batch-upload", methods=["POST"])
def batch_upload():
    """批量上传运动数据文件。"""
    user, err = require_user()
    if err:
        return err

    data = request.get_json()
    session_id = data.get("session_id", "")
    items = data.get("items", [])
    if not session_id or not items:
        return jsonify({"code": 400, "message": "缺少参数", "data": None}), 400
    if len(items) > 30:
        return jsonify({"code": 400, "message": "单次最多 30 个文件", "data": None}), 400
    if not re.match(r"^[a-f0-9]{32}$", session_id):
        return jsonify({"code": 400, "message": "无效的会话 ID", "data": None}), 400

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    session_dir = os.path.join(upload_dir, "_batch", session_id)
    if not os.path.isdir(session_dir):
        return jsonify({"code": 400, "message": "会话已过期，请重新分析", "data": None}), 400

    created = []
    errors = []

    for item in items:
        temp_id = item.get("temp_id", "")
        if not re.match(r"^[a-f0-9]+\.(tcx|gpx)$", temp_id):
            errors.append({"filename": item.get("filename"), "error": "无效的文件标识"})
            continue
        src_path = os.path.join(session_dir, temp_id)
        if not os.path.realpath(src_path).startswith(os.path.realpath(session_dir) + os.sep):
            errors.append({"filename": item.get("filename"), "error": "非法路径"})
            continue
        if not os.path.exists(src_path):
            errors.append({"filename": item.get("filename"), "error": "文件未找到"})
            continue

        try:
            is_valid, error_msg = validate_activity_file(src_path)
            if not is_valid:
                errors.append({"filename": item.get("filename"), "error": error_msg})
                continue

            parsed = parse_activity_file(src_path)
            checksum = compute_file_checksum(src_path)

            # 二次去重检查
            if Activity.objects(user=user, file_checksum=checksum).first():
                errors.append({"filename": item.get("filename"), "error": "重复文件，已跳过"})
                continue

            activity_type = item.get("activity_type", parsed.get("sport", "other"))
            if activity_type not in VALID_ACTIVITY_TYPES:
                activity_type = "other"
            name = item.get("name") or item.get("filename", "未命名")

            # 移动文件到永久位置
            ext = temp_id.rsplit(".", 1)[-1]
            safe_filename = f"{uuid.uuid4().hex}.{ext}"
            perm_path = os.path.join(upload_dir, safe_filename)
            os.rename(src_path, perm_path)

            trackpoints = parsed["trackpoints"]
            data_summary = _build_data_summary(parsed["laps"], trackpoints)

            activity = Activity(
                activity_type=activity_type,
                name=name,
                start_time=parsed["start_time"],
                source_file=safe_filename,
                source_format=ext,
                file_checksum=checksum,
                data_summary=data_summary,
                raw_data_path=perm_path,
                user=user,
            )

            if trackpoints:
                first_time = trackpoints[0]["time"]
                activity.trackpoints = [
                    Trackpoint(
                        elapsed=(tp["time"] - first_time).total_seconds(),
                        hr=tp.get("heart_rate"),
                        power=tp.get("power"),
                        speed=tp.get("speed"),
                        cadence=tp.get("cadence"),
                        altitude=tp.get("altitude"),
                        distance=tp.get("distance"),
                        latitude=tp.get("latitude"),
                        longitude=tp.get("longitude"),
                    )
                    for tp in trackpoints
                ]

            _compute_metrics(activity, parsed["trackpoints"])
            activity.save()
            created.append({"id": str(activity.id), "name": activity.name})
        except Exception as e:
            errors.append({"filename": item.get("filename"), "error": str(e)})

    # 清理会话目录
    shutil.rmtree(session_dir, ignore_errors=True)

    msg = f"成功上传 {len(created)} 条活动"
    if errors:
        msg += f"，{len(errors)} 条失败或跳过"

    return jsonify(
        {
            "code": 200,
            "message": msg,
            "data": {"created": created, "errors": errors},
        }
    )


@activities_bp.route("/activities", methods=["GET"])
def list_activities():
    """获取运动记录列表。"""
    limit = min(request.args.get("limit", 20, type=int), 100)
    offset = request.args.get("offset", 0, type=int)

    qs = _user_filter(Activity.objects().exclude("trackpoints", "raw_data_path"))
    qs = _activity_type_filter(qs)
    qs = _date_range_filter(qs)
    qs = _intensity_level_filter(qs)
    qs = _name_filter(qs)

    # 排序
    sort_field = request.args.get("sort", "-start_time")
    allowed_sorts = {"start_time", "-start_time", "created_at", "-created_at", "name", "-name"}
    if sort_field not in allowed_sorts:
        sort_field = "-start_time"

    total = qs.count()
    activities = list(qs.order_by(sort_field).skip(offset).limit(limit))

    # 计算每个活动的 PB 标记
    pb_map = _calc_pb_markers(activities, qs)

    items = []
    for a in activities:
        serialized = _serialize_activity(a)
        serialized["pb_windows"] = pb_map.get(str(a.id), [])
        items.append(serialized)

    return jsonify({"code": 200, "message": "ok", "data": {"total": total, "items": items}})


@activities_bp.route("/activities/export", methods=["GET"])
def export_activities():
    """导出活动列表为 CSV 或 JSON。"""
    qs = _user_filter(Activity.objects().exclude("trackpoints", "raw_data_path"))
    qs = _activity_type_filter(qs)
    qs = _date_range_filter(qs)
    qs = _intensity_level_filter(qs)
    qs = _name_filter(qs)
    activities = qs.order_by("-start_time")

    fmt = request.args.get("format", "csv")

    if fmt == "json":
        return jsonify(
            {
                "code": 200,
                "message": "ok",
                "data": [_serialize_activity(a) for a in activities],
            }
        )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["日期", "类型", "名称", "时长(秒)", "距离(m)", "平均功率", "TSS", "hrTSS", "强度"])

    for a in activities:
        s = a.data_summary
        m = a.computed_metrics
        writer.writerow(
            [
                a.start_time.strftime("%Y-%m-%d %H:%M"),
                a.activity_type,
                a.name or "",
                s.duration_seconds if s else "",
                round(s.total_distance, 1) if s and s.total_distance else "",
                round(s.avg_power, 0) if s and s.avg_power else "",
                round(m.tss, 1) if m and m.tss else "",
                round(m.hr_tss, 1) if m and m.hr_tss else "",
                m.intensity_level if m else "",
            ]
        )

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=activities.csv"},
    )


@activities_bp.route("/activities/<activity_id>", methods=["GET"])
def get_activity(activity_id):
    """获取单次运动记录详情。"""
    user = get_authenticated_user()
    activity = Activity.objects(id=activity_id).exclude("trackpoints", "raw_data_path").first()
    if not activity:
        return jsonify({"code": 404, "message": "运动记录不存在", "data": None}), 404
    if user and activity.user and str(activity.user.id) != str(user.id):
        return jsonify({"code": 403, "message": "无权访问", "data": None}), 403

    data = _serialize_activity(activity)

    # 单独查询 trackpoints 用于运动类型建议判断
    activity_for_check = Activity.objects(id=activity_id).first()
    data["suggested_type"] = _suggest_activity_type(activity_for_check)

    return jsonify({"code": 200, "message": "ok", "data": data})


@activities_bp.route("/activities/<activity_id>/trackpoints", methods=["GET"])
def get_trackpoints(activity_id):
    """获取活动的时间序列数据（支持降采样）。"""
    user = get_authenticated_user()
    activity = Activity.objects(id=activity_id).first()
    if not activity:
        return jsonify({"code": 404, "message": "运动记录不存在", "data": None}), 404
    if user and activity.user and str(activity.user.id) != str(user.id):
        return jsonify({"code": 403, "message": "无权访问", "data": None}), 403

    max_points = min(request.args.get("max_points", 500, type=int), 5000)
    data = activity.get_trackpoints_downsampled(max_points)
    return jsonify(
        {
            "code": 200,
            "message": "ok",
            "data": {
                "total_points": len(activity.trackpoints) if activity.trackpoints else 0,
                "points": data,
            },
        }
    )


@activities_bp.route("/activities/<activity_id>/laps", methods=["GET"])
def get_lap_splits(activity_id):
    """获取活动的分段分析。"""
    from app.services.metrics_service import calc_lap_splits

    user = get_authenticated_user()
    activity = Activity.objects(id=activity_id).first()
    if not activity:
        return jsonify({"code": 404, "message": "运动记录不存在", "data": None}), 404
    if user and activity.user and str(activity.user.id) != str(user.id):
        return jsonify({"code": 403, "message": "无权访问", "data": None}), 403

    tps = activity.trackpoints
    if not tps or len(tps) < 2:
        return jsonify({"code": 200, "message": "ok", "data": []})

    # 重建带时间的 trackpoint 数据
    from datetime import datetime, timedelta

    base_time = activity.start_time or datetime.now()
    raw_tps = []
    for tp in tps:
        raw_tps.append(
            {
                "time": base_time + timedelta(seconds=tp.elapsed),
                "distance": tp.distance,
                "heart_rate": tp.hr,
                "power": tp.power,
                "speed": tp.speed,
                "cadence": tp.cadence,
                "altitude": tp.altitude,
            }
        )

    mode = request.args.get("mode", "distance")
    interval = request.args.get("interval", 1000, type=float)

    if mode == "time":
        interval = request.args.get("interval", 300, type=float)

    laps = calc_lap_splits(raw_tps, mode=mode, interval=interval)
    return jsonify({"code": 200, "message": "ok", "data": laps})


@activities_bp.route("/activities/compare", methods=["GET"])
def compare_activities():
    """对比两个活动的指标和曲线。"""
    user = get_authenticated_user()
    id_a = request.args.get("a")
    id_b = request.args.get("b")
    if not id_a or not id_b:
        return jsonify({"code": 400, "message": "请提供两个活动 ID (a, b)", "data": None}), 400

    a = Activity.objects(id=id_a).first()
    b = Activity.objects(id=id_b).first()
    if not a or not b:
        return jsonify({"code": 404, "message": "活动不存在", "data": None}), 404
    if user:
        for act in (a, b):
            if act.user and str(act.user.id) != str(user.id):
                return jsonify({"code": 403, "message": "无权访问", "data": None}), 403

    def _tp_data(activity):
        tps = activity.get_trackpoints_downsampled(300)
        total = tps[-1]["elapsed"] if tps else 1
        return [{"percent": round(tp["elapsed"] / total * 100, 1), **tp} for tp in tps]

    return jsonify(
        {
            "code": 200,
            "message": "ok",
            "data": {
                "a": {
                    "id": str(a.id),
                    "name": a.name,
                    "type": a.activity_type,
                    "summary": _serialize_summary(a.data_summary),
                    "metrics": _serialize_metrics(a.computed_metrics),
                    "trackpoints": _tp_data(a),
                },
                "b": {
                    "id": str(b.id),
                    "name": b.name,
                    "type": b.activity_type,
                    "summary": _serialize_summary(b.data_summary),
                    "metrics": _serialize_metrics(b.computed_metrics),
                    "trackpoints": _tp_data(b),
                },
            },
        }
    )


@activities_bp.route("/activities/<activity_id>/recalculate", methods=["POST"])
def recalculate_activity(activity_id):
    """重新计算单次活动的指标（含强度等级）。"""
    user, err = require_user()
    if err:
        return err

    activity = Activity.objects(id=activity_id, user=user).first()
    if not activity:
        return jsonify({"code": 404, "message": "运动记录不存在", "data": None}), 404

    if not activity.trackpoints:
        return jsonify({"code": 400, "message": "活动无轨迹数据", "data": None}), 400

    from datetime import datetime, timedelta

    base_time = activity.start_time or datetime.now()
    raw_tps = [
        {
            "time": base_time + timedelta(seconds=tp.elapsed),
            "distance": tp.distance,
            "heart_rate": tp.hr,
            "power": tp.power,
            "speed": tp.speed,
            "cadence": tp.cadence,
            "altitude": tp.altitude,
        }
        for tp in activity.trackpoints
    ]
    _compute_metrics(activity, raw_tps)
    activity.save()
    return jsonify({"code": 200, "message": "已重新计算", "data": _serialize_activity(activity)})


@activities_bp.route("/activities/recalculate-all", methods=["POST"])
def recalculate_all_activities():
    """批量重新计算所有活动的指标。"""
    user, err = require_user()
    if err:
        return err

    from datetime import datetime, timedelta

    qs = Activity.objects(user=user)
    count = 0
    for activity in qs:
        if not activity.trackpoints:
            continue
        base_time = activity.start_time or datetime.now()
        raw_tps = [
            {
                "time": base_time + timedelta(seconds=tp.elapsed),
                "distance": tp.distance,
                "heart_rate": tp.hr,
                "power": tp.power,
                "speed": tp.speed,
                "cadence": tp.cadence,
                "altitude": tp.altitude,
            }
            for tp in activity.trackpoints
        ]
        _compute_metrics(activity, raw_tps)
        activity.save()
        count += 1

    return jsonify({"code": 200, "message": f"已重新计算 {count} 条活动", "data": {"count": count}})


@activities_bp.route("/activities/<activity_id>", methods=["PUT"])
def update_activity(activity_id):
    """更新运动记录（名称/类型）。"""
    user, err = require_user()
    if err:
        return err

    activity = Activity.objects(id=activity_id, user=user).first()
    if not activity:
        return jsonify({"code": 404, "message": "运动记录不存在", "data": None}), 404

    data = request.get_json()
    if not data:
        return jsonify({"code": 400, "message": "缺少请求体", "data": None}), 400

    if "name" in data:
        activity.name = data["name"][:200] if data["name"] else None

    if "activity_type" in data:
        if data["activity_type"] not in VALID_ACTIVITY_TYPES:
            return jsonify({"code": 400, "message": f"不支持的运动类型: {data['activity_type']}", "data": None}), 400
        old_type = activity.activity_type
        activity.activity_type = data["activity_type"]
        # 运动类型变更时重新计算指标（心率区间等可能不同）
        if old_type != data["activity_type"] and activity.trackpoints:
            from datetime import datetime, timedelta

            base_time = activity.start_time or datetime.now()
            raw_tps = [
                {
                    "time": base_time + timedelta(seconds=tp.elapsed),
                    "distance": tp.distance,
                    "heart_rate": tp.hr,
                    "power": tp.power,
                    "speed": tp.speed,
                    "cadence": tp.cadence,
                    "altitude": tp.altitude,
                }
                for tp in activity.trackpoints
            ]
            _compute_metrics(activity, raw_tps)

    if "notes" in data:
        activity.notes = data["notes"][:2000] if data["notes"] else None

    if "manual_tss" in data:
        if not activity.computed_metrics:
            from app.models.activity import ComputedMetrics

            activity.computed_metrics = ComputedMetrics()
        activity.computed_metrics.manual_tss = (
            round(float(data["manual_tss"]), 1) if data["manual_tss"] is not None else None
        )

    activity.save()
    return jsonify({"code": 200, "message": "已更新", "data": _serialize_activity(activity)})


@activities_bp.route("/activities/<activity_id>", methods=["DELETE"])
def delete_activity(activity_id):
    """删除运动记录。"""
    user, err = require_user()
    if err:
        return err

    activity = Activity.objects(id=activity_id, user=user).first()
    if not activity:
        return jsonify({"code": 404, "message": "运动记录不存在", "data": None}), 404

    if activity.raw_data_path and os.path.exists(activity.raw_data_path):
        os.remove(activity.raw_data_path)

    activity.delete()
    return jsonify({"code": 200, "message": "已删除", "data": None})


@activities_bp.route("/activities/batch-delete", methods=["POST"])
def batch_delete_activities():
    """批量删除运动记录。"""
    user, err = require_user()
    if err:
        return err

    data = request.get_json()
    if not data or "ids" not in data:
        return jsonify({"code": 400, "message": "缺少 ids 参数", "data": None}), 400

    ids = data["ids"]
    if not isinstance(ids, list) or len(ids) == 0:
        return jsonify({"code": 400, "message": "ids 必须是非空数组", "data": None}), 400
    if len(ids) > 50:
        return jsonify({"code": 400, "message": "单次最多删除 50 条", "data": None}), 400

    deleted = 0
    for aid in ids:
        activity = Activity.objects(id=aid, user=user).first()
        if activity:
            if activity.raw_data_path and os.path.exists(activity.raw_data_path):
                os.remove(activity.raw_data_path)
            activity.delete()
            deleted += 1

    return jsonify({"code": 200, "message": f"已删除 {deleted} 条记录", "data": {"deleted": deleted}})


@activities_bp.route("/activities/power-curve", methods=["GET"])
def get_power_curve():
    """获取用户的历史最佳功率/心率曲线。"""
    user, err = require_user()
    if err:
        return err

    qs = Activity.objects(user=user, computed_metrics__ne=None).only("computed_metrics", "start_time")
    activities = list(qs.order_by("-start_time").limit(200))

    curve = {"power": {}, "heart_rate": {}}
    for a in activities:
        cm = a.computed_metrics
        if not cm or not cm.best_efforts:
            continue
        for metric in ("power", "heart_rate"):
            data = cm.best_efforts.get(metric)
            if not data:
                continue
            for window_str, val in data.items():
                if val is None:
                    continue
                key = str(window_str)
                if key not in curve[metric] or val > curve[metric][key]:
                    curve[metric][key] = val

    # 按窗口时间排序
    for metric in curve:
        curve[metric] = dict(sorted(curve[metric].items(), key=lambda x: int(x[0])))

    import json as _json

    return Response(
        _json.dumps({"code": 200, "message": "ok", "data": curve}, ensure_ascii=False),
        mimetype="application/json",
    )
