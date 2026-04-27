import os
import uuid

from flask import Blueprint, current_app, jsonify, request

from app.models.activity import Activity, ComputedMetrics, DataSummary
from app.services.parse_service import parse_activity_file
from app.services.validate_service import validate_activity_file

activities_bp = Blueprint("activities", __name__)


@activities_bp.route("/activities/upload", methods=["POST"])
def upload_activity():
    """上传运动数据文件（TCX/GPX）。

    表单参数:
    - file: 运动数据文件
    - activity_type: 运动类型（cycling/indoor_cycling/running/indoor_running/walking）
    - name: 运动名称（可选）
    """
    if "file" not in request.files:
        return jsonify({"code": 400, "message": "未找到上传文件", "data": None}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"code": 400, "message": "文件名为空", "data": None}), 400

    activity_type = request.form.get("activity_type")
    if not activity_type:
        return jsonify({"code": 400, "message": "缺少 activity_type 参数", "data": None}), 400

    valid_types = ["cycling", "indoor_cycling", "running", "indoor_running", "walking", "swimming", "other"]
    if activity_type not in valid_types:
        return jsonify({"code": 400, "message": f"不支持的运动类型: {activity_type}", "data": None}), 400

    # 保存文件到 upload 目录
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)

    ext = file.filename.rsplit(".", 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)

    # 校验文件
    is_valid, error_msg = validate_activity_file(file_path)
    if not is_valid:
        os.remove(file_path)
        return jsonify({"code": 400, "message": error_msg, "data": None}), 400

    # 解析文件
    try:
        parsed = parse_activity_file(file_path)
    except (ValueError, Exception) as e:
        os.remove(file_path)
        return jsonify({"code": 422, "message": f"文件解析失败: {str(e)}", "data": None}), 422

    # 构建数据摘要
    trackpoints = parsed["trackpoints"]
    data_summary = _build_data_summary(parsed["laps"], trackpoints)

    # 计算运动名称
    name = request.form.get("name") or file.filename

    # 创建 Activity 记录（暂不绑定 user，后续加认证后再关联）
    activity = Activity(
        activity_type=activity_type,
        name=name,
        start_time=parsed["start_time"],
        source_file=filename,
        source_format=ext,
        data_summary=data_summary,
        raw_data_path=file_path,
    )

    # 计算运动指标
    _compute_metrics(activity, parsed["trackpoints"])

    activity.save()

    return jsonify({
        "code": 200,
        "message": "上传成功",
        "data": {
            "id": str(activity.id),
            "activity_type": activity.activity_type,
            "name": activity.name,
            "start_time": activity.start_time.isoformat(),
            "data_summary": _serialize_summary(data_summary),
            "computed_metrics": _serialize_metrics(activity.computed_metrics),
            "trackpoint_count": len(trackpoints),
        },
    })


def _build_data_summary(laps, trackpoints):
    """从解析数据构建 DataSummary。"""
    summary = DataSummary()

    if trackpoints:
        duration = (trackpoints[-1]["time"] - trackpoints[0]["time"]).total_seconds()
        summary.duration_seconds = int(duration)

        # 距离
        distances = [tp["distance"] for tp in trackpoints if tp.get("distance") is not None]
        if distances:
            summary.total_distance = distances[-1]

        # 心率
        hrs = [tp["heart_rate"] for tp in trackpoints if tp.get("heart_rate") is not None]
        if hrs:
            summary.avg_heart_rate = sum(hrs) // len(hrs)
            summary.max_heart_rate = max(hrs)

        # 功率
        powers = [tp["power"] for tp in trackpoints if tp.get("power") is not None]
        if powers:
            summary.avg_power = sum(powers) / len(powers)
            summary.max_power = max(powers)

        # 速度
        speeds = [tp["speed"] for tp in trackpoints if tp.get("speed") is not None]
        if speeds:
            summary.avg_speed = sum(speeds) / len(speeds)
            summary.max_speed = max(speeds)

        # 踏频
        cadences = [tp["cadence"] for tp in trackpoints if tp.get("cadence") is not None]
        if cadences:
            summary.avg_cadence = sum(cadences) // len(cadences)
            summary.max_cadence = max(cadences)

    return summary


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
        "name": activity.name,
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


def _compute_metrics(activity, trackpoints):
    """计算并填充 Activity 的 ComputedMetrics。"""
    from app.services.metrics_service import compute_activity_metrics
    from app.models.athlete_settings import AthleteParams

    # 查找生效的用户参数（当前无用户认证，取最新参数）
    params = AthleteParams.objects().order_by("-effective_date").first()
    if not params or not trackpoints:
        return

    activity_type = activity.activity_type
    hr_zones = params.get_hr_zones(activity_type)
    power_zones = params.get_power_zones() if activity_type in ("cycling", "indoor_cycling") else []

    # 获取对应运动类型的 LTHR
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


@activities_bp.route("/activities", methods=["GET"])
def list_activities():
    """获取运动记录列表。

    查询参数:
    - activity_type: 按运动类型过滤（可选）
    - limit: 返回数量，默认 20
    - offset: 偏移量，默认 0
    """
    limit = request.args.get("limit", 20, type=int)
    offset = request.args.get("offset", 0, type=int)
    limit = min(limit, 100)

    qs = Activity.objects()
    activity_type = request.args.get("activity_type")
    if activity_type:
        qs = qs.filter(activity_type=activity_type)

    activities = qs.order_by("-start_time").skip(offset).limit(limit)
    total = qs.count()

    return jsonify({
        "code": 200,
        "message": "ok",
        "data": {
            "total": total,
            "items": [_serialize_activity(a) for a in activities],
        },
    })


@activities_bp.route("/activities/<activity_id>", methods=["GET"])
def get_activity(activity_id):
    """获取单次运动记录详情。"""
    activity = Activity.objects(id=activity_id).first()
    if not activity:
        return jsonify({"code": 404, "message": "运动记录不存在", "data": None}), 404

    return jsonify({
        "code": 200,
        "message": "ok",
        "data": _serialize_activity(activity),
    })


@activities_bp.route("/activities/<activity_id>", methods=["DELETE"])
def delete_activity(activity_id):
    """删除运动记录。"""
    activity = Activity.objects(id=activity_id).first()
    if not activity:
        return jsonify({"code": 404, "message": "运动记录不存在", "data": None}), 404

    # 删除关联的源文件
    if activity.raw_data_path and os.path.exists(activity.raw_data_path):
        os.remove(activity.raw_data_path)

    activity.delete()
    return jsonify({"code": 200, "message": "已删除", "data": None})


@activities_bp.route("/pmc", methods=["GET"])
def get_pmc():
    """获取 PMC（CTL/ATL/TSB）时间序列。

    查询参数:
    - start_date: 起始日期 "YYYY-MM-DD"（默认 60 天前）
    - end_date: 结束日期 "YYYY-MM-DD"（默认今天）
    """
    from datetime import datetime as dt, timedelta

    from app.services.metrics_service import calc_daily_tss, calc_pmc

    end_date = request.args.get("end_date", dt.now().strftime("%Y-%m-%d"))
    start_date = request.args.get(
        "start_date",
        (dt.now() - timedelta(days=60)).strftime("%Y-%m-%d"),
    )

    activities = Activity.objects(
        start_time__gte=start_date,
        start_time__lte=end_date + "T23:59:59",
    )
    daily = calc_daily_tss(list(activities))
    pmc_data = calc_pmc(daily, start_date, end_date)

    return jsonify({
        "code": 200,
        "message": "ok",
        "data": pmc_data,
    })
