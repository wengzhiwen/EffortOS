import csv
import html
import io
import os
import uuid

from flask import Blueprint, Response, current_app, jsonify, request

from app.blueprints.auth.routes import require_user
from app.models.activity import Activity, DataSummary, Trackpoint
from app.services.parse_service import parse_activity_file
from app.services.validate_service import validate_activity_file

activities_bp = Blueprint("activities", __name__)

VALID_ACTIVITY_TYPES = ["cycling", "indoor_cycling", "running", "indoor_running", "walking", "swimming", "other"]

SPORT_DISPLAY = {
    "cycling": "骑行",
    "indoor_cycling": "室内骑行",
    "running": "跑步",
    "indoor_running": "室内跑步",
    "walking": "步行",
    "swimming": "游泳",
    "other": "其他",
}


def _get_authenticated_user():
    """从请求中获取已认证的用户。"""
    from app.models.user import User

    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if not token:
        token = request.cookies.get("session_token", "").strip()
    if not token:
        return None
    return User.objects(session_token=token).first()


def _user_filter(qs):
    """按当前用户过滤查询集（无用户时返回全集）。"""
    user = _get_authenticated_user()
    return qs.filter(user=user) if user else qs


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
    }


def _serialize_activity(activity):
    """将 Activity 序列化为字典。"""
    return {
        "id": str(activity.id),
        "activity_type": activity.activity_type,
        "name": html.escape(activity.name or ""),
        "start_time": activity.start_time.isoformat(),
        "source_format": activity.source_format,
        "data_summary": _serialize_summary(activity.data_summary),
        "computed_metrics": _serialize_metrics(activity.computed_metrics),
        "created_at": activity.created_at.isoformat() if activity.created_at else None,
    }


def _serialize_metrics(metrics):
    """将 ComputedMetrics 序列化为字典。"""
    if not metrics or metrics.tss is None:
        return None
    return {
        "tss": metrics.tss,
        "tss_method": metrics.tss_method,
        "hr_tss": metrics.hr_tss,
        "intensity_factor": metrics.intensity_factor,
        "hr_intensity_factor": metrics.hr_intensity_factor,
        "normalized_power": metrics.normalized_power,
        "variability_index": metrics.variability_index,
        "efficiency_factor": metrics.efficiency_factor,
        "work_kj": metrics.work_kj,
        "hr_zones_time": metrics.hr_zones_time,
        "power_zones_time": metrics.power_zones_time,
    }


# ============================================================
# 内部计算辅助
# ============================================================


def _build_data_summary(laps, trackpoints):
    """从解析数据构建 DataSummary。"""
    summary = DataSummary()

    if not trackpoints:
        return summary

    summary.duration_seconds = int((trackpoints[-1]["time"] - trackpoints[0]["time"]).total_seconds())

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
    from app.models.athlete_settings import AthleteParams
    from app.services.metrics_service import compute_activity_metrics

    current_user = _get_authenticated_user()
    qs = AthleteParams.objects()
    if current_user:
        qs = qs.filter(user=current_user)
    params = qs.order_by("-effective_date").first()
    if not params or not trackpoints:
        return

    activity_type = activity.activity_type
    hr_zones = params.get_hr_zones(activity_type)
    power_zones = params.get_power_zones() if activity_type in ("cycling", "indoor_cycling") else []

    lthr_map = {
        "cycling": params.cycling_lthr,
        "indoor_cycling": params.cycling_lthr,
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
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    trackpoints = parsed["trackpoints"]
    sport = parsed.get("sport", "other")
    start = parsed["start_time"]
    name_suggestion = f"{start.strftime('%m月%d日')}{SPORT_DISPLAY.get(sport, sport)}"

    # 数据质量检查
    total = len(trackpoints)
    hr_count = sum(1 for tp in trackpoints if tp.get("heart_rate") is not None)
    power_count = sum(1 for tp in trackpoints if tp.get("power") is not None)
    speed_count = sum(1 for tp in trackpoints if tp.get("speed") is not None)
    dist_count = sum(1 for tp in trackpoints if tp.get("distance") is not None)

    warnings = []
    if total == 0:
        warnings.append("文件中没有轨迹数据点")
    else:
        hr_pct = hr_count / total
        power_pct = power_count / total
        if hr_pct < 0.1:
            warnings.append("心率数据缺失超过 90%，无法计算心率相关指标")
        if sport in ("cycling", "indoor_cycling") and power_pct < 0.1:
            warnings.append("功率数据缺失，建议设置 FTP 后使用心率 TSS")
        if dist_count == 0 and speed_count == 0:
            warnings.append("无距离和速度数据")

    # 基础摘要
    duration = 0
    total_dist = 0
    avg_hr = 0
    if trackpoints:
        duration = int((trackpoints[-1]["time"] - trackpoints[0]["time"]).total_seconds())
        distances = [tp["distance"] for tp in trackpoints if tp.get("distance") is not None]
        if distances:
            total_dist = distances[-1]
        hrs = [tp["heart_rate"] for tp in trackpoints if tp.get("heart_rate") is not None]
        if hrs:
            avg_hr = sum(hrs) // len(hrs)

    return jsonify(
        {
            "code": 200,
            "message": "ok",
            "data": {
                "sport": sport,
                "sport_display": SPORT_DISPLAY.get(sport, sport),
                "name_suggestion": name_suggestion,
                "start_time": start.isoformat(),
                "duration_seconds": duration,
                "total_distance": round(total_dist, 1),
                "avg_heart_rate": avg_hr,
                "trackpoint_count": total,
                "has_heart_rate": hr_count > total * 0.5,
                "has_power": power_count > total * 0.5,
                "warnings": warnings,
            },
        }
    )


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

    trackpoints = parsed["trackpoints"]
    data_summary = _build_data_summary(parsed["laps"], trackpoints)
    name = request.form.get("name") or file.filename

    activity = Activity(
        activity_type=activity_type,
        name=name,
        start_time=parsed["start_time"],
        source_file=safe_filename,
        source_format=ext,
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
                "name": html.escape(activity.name or ""),
                "start_time": activity.start_time.isoformat(),
                "data_summary": _serialize_summary(data_summary),
                "computed_metrics": _serialize_metrics(activity.computed_metrics),
                "trackpoint_count": len(trackpoints),
            },
        }
    )


@activities_bp.route("/activities", methods=["GET"])
def list_activities():
    """获取运动记录列表。"""
    limit = min(request.args.get("limit", 20, type=int), 100)
    offset = request.args.get("offset", 0, type=int)

    qs = _user_filter(Activity.objects())
    qs = _activity_type_filter(qs)
    qs = _date_range_filter(qs)

    total = qs.count()
    activities = qs.order_by("-start_time").skip(offset).limit(limit)

    return jsonify(
        {"code": 200, "message": "ok", "data": {"total": total, "items": [_serialize_activity(a) for a in activities]}}
    )


@activities_bp.route("/activities/export", methods=["GET"])
def export_activities():
    """导出活动列表为 CSV。"""
    qs = _user_filter(Activity.objects())
    qs = _activity_type_filter(qs)
    qs = _date_range_filter(qs)
    activities = qs.order_by("-start_time")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["日期", "类型", "名称", "时长(秒)", "距离(m)", "平均心率", "平均功率", "TSS", "TSS方法"])

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
                s.avg_heart_rate if s else "",
                round(s.avg_power, 0) if s and s.avg_power else "",
                round(m.tss, 1) if m and m.tss else "",
                m.tss_method if m else "",
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
    activity = Activity.objects(id=activity_id).first()
    if not activity:
        return jsonify({"code": 404, "message": "运动记录不存在", "data": None}), 404

    return jsonify({"code": 200, "message": "ok", "data": _serialize_activity(activity)})


@activities_bp.route("/activities/<activity_id>/trackpoints", methods=["GET"])
def get_trackpoints(activity_id):
    """获取活动的时间序列数据（支持降采样）。"""
    activity = Activity.objects(id=activity_id).first()
    if not activity:
        return jsonify({"code": 404, "message": "运动记录不存在", "data": None}), 404

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
        activity.activity_type = data["activity_type"]

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
