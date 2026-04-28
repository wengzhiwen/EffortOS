from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.models.activity import Activity, ComputedMetrics, DataSummary
from app.models.athlete_settings import AthleteParams


def _create_activity(user, days_ago, tss=50, activity_type="cycling"):
    """创建测试活动。"""
    start = datetime.now(timezone.utc) - timedelta(days=days_ago)
    a = Activity(
        activity_type=activity_type,
        name=f"Test {days_ago}",
        start_time=start,
        data_summary=DataSummary(duration_seconds=3600),
        computed_metrics=ComputedMetrics(tss=tss, tss_method="hr"),
        user=user,
    )
    a.save()
    return a


class TestWeeklyReportAPI:
    def test_no_auth(self, client):
        r = client.post("/api/ai/weekly-report")
        assert r.status_code == 401

    @patch("app.blueprints.ai.routes.generate_weekly_report")
    def test_success(self, mock_report, client, auth_headers):
        mock_report.return_value = "这是一份周报"
        r = client.post("/api/ai/weekly-report", headers=auth_headers)
        assert r.status_code == 200
        data = r.get_json()
        assert data["code"] == 200
        assert data["data"]["report"] == "这是一份周报"

    @patch("app.blueprints.ai.routes.generate_weekly_report")
    def test_with_activities(self, mock_report, client, auth_headers, auth_token):
        from app.models.user import User

        user = User.objects(session_token=auth_token).first()
        _create_activity(user, days_ago=1, tss=80)
        mock_report.return_value = "有活动的周报"

        r = client.post("/api/ai/weekly-report", headers=auth_headers)
        assert r.status_code == 200
        data = r.get_json()
        assert data["data"]["week_activities"] >= 1

    @patch("app.blueprints.ai.routes.generate_weekly_report")
    def test_llm_error(self, mock_report, client, auth_headers):
        mock_report.side_effect = Exception("API error")
        r = client.post("/api/ai/weekly-report", headers=auth_headers)
        assert r.status_code == 500
        data = r.get_json()
        assert "失败" in data["message"]


class TestSuggestionAPI:
    def test_no_auth(self, client):
        r = client.post("/api/ai/suggestion")
        assert r.status_code == 401

    @patch("app.blueprints.ai.routes.generate_suggestion")
    def test_success(self, mock_suggest, client, auth_headers):
        mock_suggest.return_value = "建议休息"
        r = client.post(
            "/api/ai/suggestion",
            headers=auth_headers,
            json={"question": "今天该练什么？"},
        )
        assert r.status_code == 200
        data = r.get_json()
        assert data["code"] == 200
        assert data["data"]["suggestion"] == "建议休息"

    @patch("app.blueprints.ai.routes.generate_suggestion")
    def test_without_question(self, mock_suggest, client, auth_headers):
        mock_suggest.return_value = "一般性建议"
        r = client.post("/api/ai/suggestion", headers=auth_headers, json={})
        assert r.status_code == 200
        data = r.get_json()
        assert data["data"]["suggestion"] == "一般性建议"

    @patch("app.blueprints.ai.routes.generate_suggestion")
    def test_with_params(self, mock_suggest, client, auth_headers, auth_token):
        from app.models.user import User

        user = User.objects(session_token=auth_token).first()
        AthleteParams(
            user=user,
            ftp=250,
            cycling_lthr=165,
            effective_date=datetime(2026, 1, 1),
        ).save()
        _create_activity(user, days_ago=2, tss=100)
        mock_suggest.return_value = "有参数的建议"

        r = client.post("/api/ai/suggestion", headers=auth_headers, json={})
        assert r.status_code == 200

    @patch("app.blueprints.ai.routes.generate_suggestion")
    def test_llm_error(self, mock_suggest, client, auth_headers):
        mock_suggest.side_effect = ValueError("配置错误")
        r = client.post("/api/ai/suggestion", headers=auth_headers, json={})
        assert r.status_code == 400
