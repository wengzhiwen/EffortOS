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
