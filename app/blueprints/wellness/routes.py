from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from app.models.wellness import WellnessEntry
from app.utils.auth import require_user

wellness_bp = Blueprint("wellness", __name__)


def _serialize_entry(entry):
    return {
        "id": str(entry.id),
        "date": entry.date,
        "sleep_quality": entry.sleep_quality,
        "fatigue": entry.fatigue,
        "stress": entry.stress,
        "soreness": entry.soreness,
        "mood": entry.mood,
        "hrv": entry.hrv,
        "resting_hr": entry.resting_hr,
        "weight": entry.weight,
        "notes": entry.notes or "",
    }


@wellness_bp.route("/wellness", methods=["GET"])
def list_wellness():
    user, err = require_user()
    if err:
        return err

    days = min(request.args.get("days", 30, type=int), 365)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    entries = WellnessEntry.objects(user=user, date__gte=start_date, date__lte=end_date).order_by("-date")
    return jsonify({"code": 200, "message": "ok", "data": [_serialize_entry(e) for e in entries]})


@wellness_bp.route("/wellness/today", methods=["GET"])
def get_today():
    user, err = require_user()
    if err:
        return err

    today = datetime.now().strftime("%Y-%m-%d")
    entry = WellnessEntry.objects(user=user, date=today).first()
    if not entry:
        return jsonify({"code": 200, "message": "ok", "data": None})

    return jsonify({"code": 200, "message": "ok", "data": _serialize_entry(entry)})


@wellness_bp.route("/wellness", methods=["POST"])
def create_or_update_wellness():
    user, err = require_user()
    if err:
        return err

    data = request.get_json()
    if not data or not data.get("date"):
        return jsonify({"code": 400, "message": "日期为必填项", "data": None}), 400

    date = data["date"]
    entry = WellnessEntry.objects(user=user, date=date).first()

    fields = ("sleep_quality", "fatigue", "stress", "soreness", "mood", "hrv", "resting_hr", "weight", "notes")

    if entry:
        for f in fields:
            if f in data:
                setattr(entry, f, data[f])
        entry.save()
    else:
        kwargs = {"user": user, "date": date}
        for f in fields:
            if f in data:
                kwargs[f] = data[f]
        entry = WellnessEntry(**kwargs)
        entry.save()

    return jsonify({"code": 200, "message": "保存成功", "data": _serialize_entry(entry)})


@wellness_bp.route("/wellness/<entry_id>", methods=["DELETE"])
def delete_wellness(entry_id):
    user, err = require_user()
    if err:
        return err

    entry = WellnessEntry.objects(id=entry_id, user=user).first()
    if not entry:
        return jsonify({"code": 404, "message": "记录不存在", "data": None}), 404

    entry.delete()
    return jsonify({"code": 200, "message": "已删除", "data": None})
