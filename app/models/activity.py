from datetime import datetime, timezone

from mongoengine import (
    DateTimeField,
    DictField,
    EmbeddedDocument,
    EmbeddedDocumentField,
    EmbeddedDocumentListField,
    FloatField,
    IntField,
    ReferenceField,
    StringField,
)

from app.models.base import BaseDocument


class DataSummary(EmbeddedDocument):
    """原始数据摘要：时间序列的关键统计值。"""

    duration_seconds = IntField()  # 运动时长（秒，排除暂停）
    active_seconds = IntField()  # deprecated, kept for backward compat
    meta = {"strict": False}
    total_distance = FloatField()  # 总距离（米）
    avg_heart_rate = IntField()  # 平均心率
    max_heart_rate = IntField()  # 最大心率
    avg_power = FloatField()  # 平均功率
    max_power = FloatField()  # 最大功率
    avg_speed = FloatField()  # 平均速度（m/s）
    max_speed = FloatField()  # 最大速度（m/s）
    avg_cadence = IntField()  # 平均踏频
    max_cadence = IntField()  # 最大踏频
    elevation_gain = FloatField()  # 累计爬升（米）
    elevation_loss = FloatField()  # 累计下降（米）


class ComputedMetrics(EmbeddedDocument):
    """计算得出的运动指标。"""

    tss = FloatField()  # 功率 TSS（仅功率有效时有值）
    hr_tss = FloatField()  # 基于心率的 TSS
    manual_tss = FloatField()  # 用户手动设定的 TSS（优先于计算值）
    intensity_factor = FloatField()  # 强度因子（IF = NP/FTP）
    hr_intensity_factor = FloatField()  # 心率强度因子（HR_IF = avg_hr/LTHR）
    normalized_power = FloatField()  # 标准化功率（NP）
    variability_index = FloatField()  # 变异性指数（VI = NP/avg_power）
    efficiency_factor = FloatField()  # 效率因子（EF = NP/avg_hr 或 avg_speed/avg_hr）
    work_kj = FloatField()  # 总做功（kJ）
    tss_method = StringField()  # TSS 方法标记："power" / "hr" / null
    intensity_level = StringField()  # 强度分类："recovery"/"endurance"/"tempo"/"threshold"/"vo2max"
    intensity_reason = DictField()  # 分类依据 {"method":"power|hr","strict":bool,"zone_times":{...},"matched":描述}
    hr_zones_time = DictField()  # 心率区间时间分布 {"Z1": 秒数, ...}
    power_zones_time = DictField()  # 功率区间时间分布 {"Z1": 秒数, ...}
    best_efforts = DictField()  # 最佳表现 {"power": {5: 450, ...}, "heart_rate": {5: 178, ...}}


class Trackpoint(EmbeddedDocument):
    """单个时间序列数据点。"""

    elapsed = FloatField(required=True)  # 距开始的秒数
    hr = IntField()  # 心率
    power = IntField()  # 功率
    speed = FloatField()  # 速度 (m/s)
    cadence = IntField()  # 踏频
    altitude = FloatField()  # 海拔
    distance = FloatField()  # 累计距离
    latitude = FloatField()  # 纬度
    longitude = FloatField()  # 经度


class Activity(BaseDocument):
    user = ReferenceField("User")
    gear = ReferenceField("Gear")  # 关联装备
    activity_type = StringField(
        required=True,
        choices=["cycling", "indoor_cycling", "running", "indoor_running", "walking", "swimming", "other"],
    )
    name = StringField(max_length=200)
    notes = StringField()  # 用户备注/感受记录
    start_time = DateTimeField(required=True)
    source_file = StringField()  # 原始文件路径
    source_format = StringField(choices=["tcx", "gpx"])  # 文件格式

    data_summary = EmbeddedDocumentField(DataSummary)
    computed_metrics = EmbeddedDocumentField(ComputedMetrics)
    trackpoints = EmbeddedDocumentListField(Trackpoint)

    # 原始时间序列数据引用（大文件存于文件系统）
    raw_data_path = StringField()

    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    meta = {
        "collection": "activities",
        "indexes": ["user", "start_time", "activity_type", ("user", "start_time"), ("user", "activity_type")],
    }

    def get_trackpoints_downsampled(self, max_points=500):
        """返回降采样后的 trackpoint 数据。"""
        tps = self.trackpoints
        if not tps:
            return []
        total = len(tps)
        fields = {
            "elapsed": lambda tp: tp.elapsed,
            "hr": lambda tp: tp.hr,
            "power": lambda tp: tp.power,
            "speed": lambda tp: tp.speed,
            "cadence": lambda tp: tp.cadence,
            "altitude": lambda tp: tp.altitude,
            "distance": lambda tp: tp.distance,
            "latitude": lambda tp: tp.latitude,
            "longitude": lambda tp: tp.longitude,
        }
        if total <= max_points:
            return [{k: fn(tp) for k, fn in fields.items()} for tp in tps]
        step = total / max_points
        return [{k: fn(tps[int(i * step)]) for k, fn in fields.items()} for i in range(max_points)]

    def __str__(self):
        return f"Activity({self.activity_type} @ {self.start_time})"
