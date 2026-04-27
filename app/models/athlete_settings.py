from mongoengine import (
    DictField,
    FloatField,
    IntField,
    ReferenceField,
)

from app.models.base import BaseDocument


class AthleteSettings(BaseDocument):
    """运动员配置：心率区间、功率区间、关键阈值。"""

    user = ReferenceField("User", required=True, unique=True)

    # 心率区间阈值（bpm），5 个阈值定义 Z1-Z5
    # Z1: < hr_zones[0], Z2: hr_zones[0]-hr_zones[1], ..., Z5: >= hr_zones[3]
    hr_zones = DictField(
        default={
            "z1_max": 120,
            "z2_max": 150,
            "z3_max": 165,
            "z4_max": 175,
            "z5_max": 190,
        }
    )

    # 功率区间阈值（W），基于 FTP 百分比
    power_zones = DictField(
        default={
            "z1_max": 55,   # < 55% FTP（恢复区）
            "z2_max": 75,   # 55-75% FTP（耐力区）
            "z3_max": 90,   # 75-90% FTP（节奏区）
            "z4_max": 105,  # 90-105% FTP（阈值区）
            "z5_max": 120,  # 105-120% FTP（VO2max 区）
            "z6_max": 150,  # 120-150% FTP（无氧区）
            "z7_max": 999,  # >= 150% FTP（神经肌肉区）
        }
    )

    # 关键参数
    ftp = IntField(default=200)  # 功能阈值功率（W）
    max_heart_rate = IntField(default=190)  # 最大心率（bpm）
    lthr = IntField()  # 乳酸阈值心率（bpm）
    weight = FloatField()  # 体重（kg）

    meta = {
        "collection": "athlete_settings",
        "indexes": ["user"],
    }

    def __str__(self):
        return f"AthleteSettings(ftp={self.ftp}, max_hr={self.max_heart_rate})"
