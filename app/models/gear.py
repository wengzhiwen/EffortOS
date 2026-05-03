from datetime import datetime, timezone

from mongoengine import DateTimeField, FloatField, ReferenceField, StringField

from app.models.base import BaseDocument


class Gear(BaseDocument):
    user = ReferenceField("User", required=True)
    name = StringField(required=True, max_length=100)
    gear_type = StringField(
        required=True,
        choices=["bike", "shoes", "wetsuit", "other"],
    )
    purchase_date = StringField()  # YYYY-MM-DD
    distance_limit_km = FloatField()  # 寿命里程阈值（km），达到后提醒更换
    total_distance_km = FloatField(default=0)  # 累计里程（km）
    notes = StringField()
    is_active = StringField(default="active")  # active / retired

    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
