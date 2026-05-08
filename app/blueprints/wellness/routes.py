from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from app.models.activity import Activity
from app.models.wellness import WellnessEntry
from app.services.i18n_service import t
from app.services.metrics_service import calc_daily_tss
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
        return jsonify({"code": 400, "message": t("api.date_required"), "data": None}), 400

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

    return jsonify({"code": 200, "message": t("api.save_success"), "data": _serialize_entry(entry)})


@wellness_bp.route("/wellness/<entry_id>", methods=["DELETE"])
def delete_wellness(entry_id):
    user, err = require_user()
    if err:
        return err

    entry = WellnessEntry.objects(id=entry_id, user=user).first()
    if not entry:
        return jsonify({"code": 404, "message": t("api.record_not_found"), "data": None}), 404

    entry.delete()
    return jsonify({"code": 200, "message": t("api.deleted"), "data": None})


@wellness_bp.route("/wellness/readiness", methods=["GET"])
def get_readiness():
    """计算今日准备度（Readiness）。

    基于主观感受（睡眠/疲劳/压力/酸痛/心情）和近期训练负荷综合计算。
    满分 100，越高表示准备度越好。
    """
    user, err = require_user()
    if err:
        return err

    today = datetime.now().strftime("%Y-%m-%d")
    entry = WellnessEntry.objects(user=user, date=today).first()

    # 主观感受分（满分 50）
    subjective_score = 0
    subjective_fields = 0

    if entry:
        # 睡眠和心情正向（越高越好）
        if entry.sleep_quality:
            subjective_score += entry.sleep_quality * 2.5  # 满分 12.5
            subjective_fields += 1
        if entry.mood:
            subjective_score += entry.mood * 2.5  # 满分 12.5
            subjective_fields += 1
        # 疲劳、压力、酸痛反向（越低越好，5→0, 1→4）
        if entry.fatigue:
            subjective_score += (6 - entry.fatigue) * 2.5  # 满分 12.5
            subjective_fields += 1
        if entry.stress:
            subjective_score += (6 - entry.stress) * 1.5  # 满分 7.5
            subjective_fields += 1
        if entry.soreness:
            subjective_score += (6 - entry.soreness) * 1.5  # 满分 7.5
            subjective_fields += 1

    # 训练负荷分（满分 50）：基于近 7 天 TSS
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    activities = Activity.objects(user=user, start_time__gte=week_ago)
    daily = calc_daily_tss(list(activities))
    week_tss = sum(daily.values())

    # TSS 负荷评分：0 TSS → 50 分（充分休息），> 600 TSS → 0 分（过度训练）
    if week_tss <= 300:
        load_score = 50
    elif week_tss <= 600:
        load_score = 50 - (week_tss - 300) / 300 * 30
    else:
        load_score = max(0, 20 - (week_tss - 600) / 400 * 20)

    total = subjective_score + load_score
    total = round(min(max(total, 0), 100))

    # 准备度等级
    if total >= 80:
        level = "excellent"
        label = t("api.readiness_excellent")
    elif total >= 60:
        level = "good"
        label = t("api.readiness_good")
    elif total >= 40:
        level = "moderate"
        label = t("api.readiness_moderate")
    elif total >= 20:
        level = "low"
        label = t("api.readiness_low")
    else:
        level = "rest"
        label = t("api.readiness_rest")

    return jsonify(
        {
            "code": 200,
            "message": "ok",
            "data": {
                "score": total,
                "level": level,
                "label": label,
                "subjective_score": round(subjective_score),
                "load_score": round(load_score),
                "week_tss": round(week_tss, 1),
                "has_wellness_entry": entry is not None,
            },
        }
    )
