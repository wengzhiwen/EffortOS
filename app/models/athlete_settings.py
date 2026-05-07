from datetime import datetime, timezone

from mongoengine import DateTimeField, FloatField, IntField, ReferenceField

from app.models.base import BaseDocument


class AthleteParams(BaseDocument):
    """运动员关键参数，按日期生效。

    每条记录代表从 effective_date 开始生效的参数快照。
    参数变更后，该日期之后的所有 Activity 可能需要重算。
    """

    user = ReferenceField("User", required=True)
    effective_date = DateTimeField(required=True)  # 生效日期

    # 骑行参数
    ftp = IntField()  # 功能阈值功率（W），仅骑行
    cycling_lthr = IntField()  # 骑行阈值心率（bpm）

    # 跑步参数
    running_lthr = IntField()  # 跑步阈值心率（bpm）

    # 步行参数
    walking_lthr = IntField()  # 步行阈值心率（bpm）

    # 通用参数
    max_heart_rate = IntField()  # 最大心率（bpm）
    weight = FloatField()  # 体重（kg）

    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    meta = {
        "collection": "athlete_params",
        "indexes": ["user", "effective_date"],
        "ordering": ["-effective_date"],
    }

    def __str__(self):
        return f"AthleteParams(date={self.effective_date}, ftp={self.ftp})"

    def get_hr_zones(self, sport: str) -> list[dict]:
        """根据运动类型和阈值心率自动推算心率分区（基于 LTHR 百分比）。

        返回 [{"name": "Z1", "min": 0, "max": X}, ...]
        """
        lthr_map = {
            "cycling": self.cycling_lthr,
            "indoor_cycling": self.cycling_lthr,
            "commute_cycling": self.cycling_lthr,
            "running": self.running_lthr,
            "indoor_running": self.running_lthr,
            "walking": self.walking_lthr,
        }
        lthr = lthr_map.get(sport)
        if not lthr:
            # 无 LTHR 时，基于最大心率估算（LTHR ≈ 85% 最大心率）
            if self.max_heart_rate:
                lthr = int(self.max_heart_rate * 0.85)
            else:
                return []

        # 基于 Joe Friel 的心率分区（LTHR 百分比）
        zones = [
            {"name": "Z1", "min": 0, "max": int(lthr * 0.68)},  # 恢复区
            {"name": "Z2", "min": int(lthr * 0.68), "max": int(lthr * 0.83)},  # 有氧区
            {"name": "Z3", "min": int(lthr * 0.83), "max": int(lthr * 0.94)},  # 节奏区
            {"name": "Z4", "min": int(lthr * 0.94), "max": int(lthr * 1.05)},  # 阈值区
            {"name": "Z5", "min": int(lthr * 1.05), "max": 999},  # VO2max+
        ]
        return zones

    def get_power_zones(self) -> list[dict]:
        """基于 FTP 自动推算功率分区（Coggan 经典 7 区）。

        仅适用于骑行。无 FTP 时返回空列表。
        """
        if not self.ftp:
            return []

        zones = [
            {"name": "Z1", "min": 0, "max": int(self.ftp * 0.55)},  # 恢复区
            {"name": "Z2", "min": int(self.ftp * 0.55), "max": int(self.ftp * 0.75)},  # 耐力区
            {"name": "Z3", "min": int(self.ftp * 0.75), "max": int(self.ftp * 0.90)},  # 节奏区
            {"name": "Z4", "min": int(self.ftp * 0.90), "max": int(self.ftp * 1.05)},  # 阈值区
            {"name": "Z5", "min": int(self.ftp * 1.05), "max": int(self.ftp * 1.20)},  # VO2max 区
            {"name": "Z6", "min": int(self.ftp * 1.20), "max": int(self.ftp * 1.50)},  # 无氧区
            {"name": "Z7", "min": int(self.ftp * 1.50), "max": 9999},  # 神经肌肉区
        ]
        return zones
