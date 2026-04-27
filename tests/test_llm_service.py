from app.services.llm_service import (
    analyze_activity_distribution,
    analyze_training_load,
    analyze_weekly_volume,
)


class TestAnalyzeTrainingLoad:
    def test_tsb_very_fresh(self):
        result = analyze_training_load(50, 20, 30)
        assert result["tsb_level"] == "非常清新"
        assert "不足" in result["tsb_advice"]

    def test_tsb_fresh(self):
        result = analyze_training_load(50, 35, 15)
        assert result["tsb_level"] == "清新"
        assert "比赛" in result["tsb_advice"]

    def test_tsb_neutral(self):
        result = analyze_training_load(50, 50, 0)
        assert result["tsb_level"] == "中性"

    def test_tsb_fatigued(self):
        result = analyze_training_load(50, 65, -15)
        assert result["tsb_level"] == "疲劳"
        assert result["tsb_risk"] == "注意恢复"

    def test_tsb_overtrained(self):
        result = analyze_training_load(50, 90, -40)
        assert result["tsb_level"] == "过度疲劳"
        assert "过度训练" in result["tsb_risk"]
        assert "⚠️" in result["tsb_advice"]

    def test_ctl_levels(self):
        assert analyze_training_load(10, 10, 0)["ctl_level"] == "低训练负荷"
        assert analyze_training_load(35, 35, 0)["ctl_level"] == "中等训练负荷"
        assert analyze_training_load(65, 65, 0)["ctl_level"] == "高训练负荷"
        assert analyze_training_load(90, 90, 0)["ctl_level"] == "极高训练负荷"

    def test_ratio_assessment(self):
        # 高比率：急性负荷远高于慢性
        result = analyze_training_load(20, 50, -30)
        assert "突增" in result["ratio_assessment"]

        # 平衡
        result = analyze_training_load(50, 50, 0)
        assert "平衡" in result["ratio_assessment"]

        # 恢复阶段
        result = analyze_training_load(50, 30, 20)
        assert "恢复" in result["ratio_assessment"] or "减量" in result["ratio_assessment"]


class TestAnalyzeWeeklyVolume:
    def test_no_history(self):
        result = analyze_weekly_volume(300, 5)
        assert result["total_tss"] == 300
        assert result["training_count"] == 5
        assert "历史" in result["volume_change"]

    def test_high_increase(self):
        result = analyze_weekly_volume(400, 5, avg_weekly_tss=250)
        assert "高" in result["volume_change"]
        assert "60%" in result["volume_change"]

    def test_normal(self):
        result = analyze_weekly_volume(260, 4, avg_weekly_tss=250)
        assert "持平" in result["volume_change"]

    def test_low_frequency(self):
        result = analyze_weekly_volume(100, 2)
        assert "偏低" in result["frequency_assessment"]

    def test_zero(self):
        result = analyze_weekly_volume(0, 0)
        assert "无训练" in result["frequency_assessment"]


class TestAnalyzeActivityDistribution:
    def test_single_type(self):
        activities = [
            {"activity_type": "cycling", "computed_metrics": {"tss": 100}},
            {"activity_type": "cycling", "computed_metrics": {"tss": 100}},
            {"activity_type": "cycling", "computed_metrics": {"tss": 100}},
            {"activity_type": "cycling", "computed_metrics": {"tss": 100}},
        ]
        result = analyze_activity_distribution(activities)
        assert "单一" in result["diversity"]

    def test_diverse(self):
        activities = [
            {"activity_type": "cycling", "computed_metrics": {"tss": 100}},
            {"activity_type": "running", "computed_metrics": {"tss": 80}},
            {"activity_type": "walking", "computed_metrics": {"tss": 30}},
        ]
        result = analyze_activity_distribution(activities)
        assert "多样化" in result["diversity"]

    def test_empty(self):
        result = analyze_activity_distribution([])
        assert "无训练" in result["diversity"]
