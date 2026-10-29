"""API contract tests, run against the real committed parquet snapshot.

These intentionally do not mock the cache layer: the committed snapshot is part of the
product (the brief requires the demo to work offline), so the contract tests double as
a check that the snapshot itself still supports every endpoint end-to-end.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealth:
    def test_returns_ok(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestForecastEndpoint:
    def test_mid_month_date_returns_48_periods(self):
        response = client.get("/api/forecast", params={"date": "2026-01-15"})
        assert response.status_code == 200
        body = response.json()
        assert len(body["periods"]) == 48
        assert body["date"] == "2026-01-15"
        assert body["total_forecast_mwh"] > 0
        # Safe volume must be <= forecast - it's a conservative haircut, not a boost.
        assert body["total_safe_volume_mwh"] <= body["total_forecast_mwh"]

    def test_first_day_of_month_exercises_the_lookback_buffer(self):
        # 2026-01-01's decision-time forecast is selected from WINDFOR publishes on
        # 2025-12-31, which only exist because the cache was fetched with a lookback
        # buffer before the January analysis scope.
        response = client.get("/api/forecast", params={"date": "2026-01-01"})
        assert response.status_code == 200
        assert response.json()["decision_publish_time"].startswith("2025-12-31")

    def test_date_outside_cached_scope_returns_404(self):
        response = client.get("/api/forecast", params={"date": "2026-02-01"})
        assert response.status_code == 404
        assert "error" in response.json()

    def test_invalid_date_format_returns_422(self):
        response = client.get("/api/forecast", params={"date": "not-a-date"})
        assert response.status_code == 422

    def test_confidence_out_of_bounds_returns_422(self):
        response = client.get(
            "/api/forecast", params={"date": "2026-01-15", "confidence": 1.0}
        )
        assert response.status_code == 422


class TestActualsEndpoint:
    def test_returns_periods_in_range(self):
        response = client.get(
            "/api/actuals", params={"from": "2026-01-01", "to": "2026-01-02"}
        )
        assert response.status_code == 200
        body = response.json()
        assert len(body["periods"]) == 96  # 2 days * 48 periods

    def test_from_after_to_returns_400(self):
        response = client.get(
            "/api/actuals", params={"from": "2026-01-31", "to": "2026-01-01"}
        )
        assert response.status_code == 400

    def test_range_with_no_data_returns_empty_list(self):
        response = client.get(
            "/api/actuals", params={"from": "2030-01-01", "to": "2030-01-02"}
        )
        assert response.status_code == 200
        assert response.json()["periods"] == []


class TestComparisonEndpoint:
    def test_returns_joined_series(self):
        response = client.get(
            "/api/comparison", params={"from": "2026-01-01", "to": "2026-01-01"}
        )
        assert response.status_code == 200
        body = response.json()
        assert len(body["periods"]) == 48
        first = body["periods"][0]
        assert set(["actual_mw", "forecast_mw", "error_mw", "horizon_hours"]) <= set(first)
        assert first["error_mw"] == first["actual_mw"] - first["forecast_mw"]


class TestAccuracyEndpoint:
    def test_returns_overall_and_all_slices(self):
        response = client.get(
            "/api/accuracy", params={"from": "2026-01-01", "to": "2026-01-31"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["overall"]["count"] == 1488
        assert len(body["by_settlement_period"]) == 48
        assert len(body["by_day"]) == 31
        assert len(body["by_actual_decile"]) == 10
        assert body["by_horizon_bucket"]

    def test_default_confidence_matches_settings(self):
        response = client.get(
            "/api/accuracy", params={"from": "2026-01-01", "to": "2026-01-31"}
        )
        assert response.json()["confidence"] == 0.9

    def test_range_with_no_data_returns_404(self):
        response = client.get(
            "/api/accuracy", params={"from": "2030-01-01", "to": "2030-01-02"}
        )
        assert response.status_code == 404
