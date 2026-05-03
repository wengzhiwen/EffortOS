from datetime import datetime, timezone

from mongoengine import DateTimeField, FloatField, IntField, ReferenceField, StringField

from app.models.base import BaseDocument


class WellnessEntry(BaseDocument):
    user = ReferenceField("User", required=True)
    date = StringField(required=True)  # YYYY-MM-DD，唯一键
    sleep_quality = IntField(min_value=1, max_value=5)  # 睡眠质量 1-5
    fatigue = IntField(min_value=1, max_value=5)  # 疲劳度 1-5
    stress = IntField(min_value=1, max_value=5)  # 压力 1-5
    soreness = IntField(min_value=1, max_value=5)  # 肌肉酸痛 1-5
    mood = IntField(min_value=1, max_value=5)  # 心情 1-5
    hrv = FloatField()  # HRV（毫秒）
    resting_hr = IntField()  # 静息心率
    weight = FloatField()  # 体重（kg）
    notes = StringField()  # 备注

    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    meta = {"collection": "wellness", "indexes": ["user", "date", {"fields": ["user", "date"], "unique": True}]}
