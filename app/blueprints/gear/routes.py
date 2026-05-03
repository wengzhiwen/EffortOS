from flask import Blueprint, jsonify, request

from app.models.gear import Gear
from app.utils.auth import require_user

gear_bp = Blueprint("gear", __name__)

GEAR_TYPE_NAMES = {"bike": "自行车", "shoes": "跑鞋", "wetsuit": "防寒服", "other": "其他"}


def _serialize_gear(gear):
    return {
        "id": str(gear.id),
        "name": gear.name,
        "gear_type": gear.gear_type,
        "gear_type_name": GEAR_TYPE_NAMES.get(gear.gear_type, gear.gear_type),
        "purchase_date": gear.purchase_date,
        "distance_limit_km": gear.distance_limit_km,
        "total_distance_km": round(gear.total_distance_km or 0, 1),
        "notes": gear.notes or "",
        "is_active": gear.is_active,
        "wear_percent": round((gear.total_distance_km or 0) / gear.distance_limit_km * 100, 1)
        if gear.distance_limit_km
        else None,
        "needs_replacement": (gear.total_distance_km or 0) >= gear.distance_limit_km
        if gear.distance_limit_km
        else False,
    }


@gear_bp.route("/gear", methods=["GET"])
def list_gear():
    user, err = require_user()
    if err:
        return err
    gears = Gear.objects(user=user).order_by("-is_active", "-created_at")
    return jsonify({"code": 200, "message": "ok", "data": [_serialize_gear(g) for g in gears]})


@gear_bp.route("/gear", methods=["POST"])
def create_gear():
    user, err = require_user()
    if err:
        return err
    data = request.get_json()
    if not data or not data.get("name") or not data.get("gear_type"):
        return jsonify({"code": 400, "message": "名称和类型为必填项", "data": None}), 400

    gear = Gear(
        user=user,
        name=data["name"],
        gear_type=data["gear_type"],
        purchase_date=data.get("purchase_date"),
        distance_limit_km=data.get("distance_limit_km"),
        notes=data.get("notes", ""),
    )
    gear.save()
    return jsonify({"code": 200, "message": "创建成功", "data": _serialize_gear(gear)})


@gear_bp.route("/gear/<gear_id>", methods=["PUT"])
def update_gear(gear_id):
    user, err = require_user()
    if err:
        return err
    gear = Gear.objects(id=gear_id, user=user).first()
    if not gear:
        return jsonify({"code": 404, "message": "装备不存在", "data": None}), 404

    data = request.get_json()
    if not data:
        return jsonify({"code": 400, "message": "请求数据为空", "data": None}), 400

    for field in ("name", "gear_type", "purchase_date", "distance_limit_km", "notes", "is_active"):
        if field in data:
            setattr(gear, field, data[field])
    gear.save()
    return jsonify({"code": 200, "message": "更新成功", "data": _serialize_gear(gear)})


@gear_bp.route("/gear/<gear_id>", methods=["DELETE"])
def delete_gear(gear_id):
    user, err = require_user()
    if err:
        return err
    gear = Gear.objects(id=gear_id, user=user).first()
    if not gear:
        return jsonify({"code": 404, "message": "装备不存在", "data": None}), 404

    gear.delete()
    return jsonify({"code": 200, "message": "已删除", "data": None})
