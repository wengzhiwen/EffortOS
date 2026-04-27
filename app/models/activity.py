from datetime import datetime, timezone

from mongoengine import (
    DateTimeField,
    DictField,
    EmbeddedDocument,
    EmbeddedDocumentField,
    FloatField,
    IntField,
    ReferenceField,
    StringField,
)

from app.models.base import BaseDocument


class DataSummary(EmbeddedDocument):
    """原始数据摘要：时间序列的关键统计值。"""

    duration_seconds = IntField()  # 总时长（秒）
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

    tss = FloatField()  # 训练压力分数（实际使用的值）
    hr_tss = FloatField()  # 基于心率的 TSS
    intensity_factor = FloatField()  # 强度因子（IF = NP/FTP）
    hr_intensity_factor = FloatField()  # 心率强度因子（HR_IF = avg_hr/LTHR）
    normalized_power = FloatField()  # 标准化功率（NP）
    variability_index = FloatField()  # 变异性指数（VI = NP/avg_power）
    efficiency_factor = FloatField()  # 效率因子（EF = NP/avg_hr 或 avg_speed/avg_hr）
    work_kj = FloatField()  # 总做功（kJ）
    tss_method = StringField()  # TSS 方法标记："power" / "hr" / null
    hr_zones_time = DictField()  # 心率区间时间分布 {"Z1": 秒数, ...}
    power_zones_time = DictField()  # 功率区间时间分布 {"Z1": 秒数, ...}


class Activity(BaseDocument):
    user = ReferenceField("User")
    activity_type = StringField(
        required=True,
        choices=["cycling", "indoor_cycling", "running", "indoor_running", "walking", "swimming", "other"],
    )
    name = StringField(max_length=200)
    start_time = DateTimeField(required=True)
    source_file = StringField()  # 原始文件路径
    source_format = StringField(choices=["tcx", "gpx"])  # 文件格式

    data_summary = EmbeddedDocumentField(DataSummary)
    computed_metrics = EmbeddedDocumentField(ComputedMetrics)

    # 原始时间序列数据引用（大文件存于文件系统）
    raw_data_path = StringField()

    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    meta = {
        "collection": "activities",
        "indexes": ["user", "start_time", "activity_type"],
    }

    def __str__(self):
        return f"Activity({self.activity_type} @ {self.start_time})"
