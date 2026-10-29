from datetime import UTC, date, datetime

import pandas as pd
import pytest

from app.services.decision_forecast import (
    DecisionRuleConfig,
    NoEligibleForecastError,
    build_decision_time_series,
    decision_cutoff_utc,
    select_decision_publish_time,
)
from tests.fixtures import make_fuelhh_df, make_windfor_df

DEFAULT_CONFIG = DecisionRuleConfig(
    cutoff_time="11:00", cutoff_timezone="Europe/London", days_before=1
)


class TestDecisionCutoffUtc:
    def test_gmt_date_cutoff_is_11_00_utc(self):
        # January is GMT (UTC+0) in the UK - 11:00 local should equal 11:00 UTC.
        cutoff = decision_cutoff_utc(date(2026, 1, 15), DEFAULT_CONFIG)
        assert cutoff == datetime(2026, 1, 14, 11, 0, tzinfo=UTC)

    def test_bst_date_cutoff_is_10_00_utc(self):
        # Mid-July is BST (UTC+1) - 11:00 local is 10:00 UTC. This proves the rule
        # uses real timezone conversion (zoneinfo) rather than a hardcoded UTC+0
        # offset that would only happen to be correct for the January 2026 scope.
        cutoff = decision_cutoff_utc(date(2026, 7, 15), DEFAULT_CONFIG)
        assert cutoff == datetime(2026, 7, 14, 10, 0, tzinfo=UTC)

    def test_days_before_is_configurable(self):
        config = DecisionRuleConfig(
            cutoff_time="11:00", cutoff_timezone="Europe/London", days_before=2
        )
        cutoff = decision_cutoff_utc(date(2026, 1, 15), config)
        assert cutoff == datetime(2026, 1, 13, 11, 0, tzinfo=UTC)

    def test_cutoff_time_is_configurable(self):
        config = DecisionRuleConfig(
            cutoff_time="09:30", cutoff_timezone="Europe/London", days_before=1
        )
        cutoff = decision_cutoff_utc(date(2026, 1, 15), config)
        assert cutoff == datetime(2026, 1, 14, 9, 30, tzinfo=UTC)


class TestSelectDecisionPublishTime:
    def test_picks_latest_publish_strictly_before_cutoff(self):
        publish_times = pd.Series(
            pd.to_datetime(
                ["2026-01-14T09:30:00Z", "2026-01-14T10:59:00Z", "2026-01-14T11:30:00Z"],
                utc=True,
            )
        )
        cutoff = datetime(2026, 1, 14, 11, 0, tzinfo=UTC)
        chosen = select_decision_publish_time(publish_times, cutoff)
        assert chosen == pd.Timestamp("2026-01-14T10:59:00Z")

    def test_publish_exactly_at_cutoff_is_excluded(self):
        # A forecast published at exactly 11:00:00 was not yet available at gate
        # closure, so it must not be selected even though it is not "after" either.
        publish_times = pd.Series(
            pd.to_datetime(["2026-01-14T10:00:00Z", "2026-01-14T11:00:00Z"], utc=True)
        )
        cutoff = datetime(2026, 1, 14, 11, 0, tzinfo=UTC)
        chosen = select_decision_publish_time(publish_times, cutoff)
        assert chosen == pd.Timestamp("2026-01-14T10:00:00Z")

    def test_raises_when_no_eligible_publish(self):
        publish_times = pd.Series(pd.to_datetime(["2026-01-14T12:00:00Z"], utc=True))
        cutoff = datetime(2026, 1, 14, 11, 0, tzinfo=UTC)
        with pytest.raises(NoEligibleForecastError):
            select_decision_publish_time(publish_times, cutoff)


class TestBuildDecisionTimeSeries:
    def test_selects_pre_cutoff_run_and_broadcasts_hourly_to_half_hours(self):
        # Delivery day 2026-01-15 -> cutoff is 2026-01-14T11:00:00Z (GMT).
        # Two settlement periods (00:00 and 00:30) both fall in the 00:00 clock hour.
        fuelhh = make_fuelhh_df(
            [
                {
                    "settlementDate": "2026-01-15",
                    "settlementPeriod": 1,
                    "startTime": "2026-01-15T00:00:00Z",
                    "generation": 1000.0,
                },
                {
                    "settlementDate": "2026-01-15",
                    "settlementPeriod": 2,
                    "startTime": "2026-01-15T00:30:00Z",
                    "generation": 1050.0,
                },
            ]
        )
        windfor = make_windfor_df(
            [
                # Eligible run (before cutoff): the one that must be used.
                {
                    "publishTime": "2026-01-14T09:30:00Z",
                    "startTime": "2026-01-15T00:00:00Z",
                    "generation": 900.0,
                },
                # A later run on the same morning, published AFTER cutoff - using
                # this would leak information the desk didn't have, so it must be
                # ignored even though it's "more accurate" for this synthetic case.
                {
                    "publishTime": "2026-01-14T11:30:00Z",
                    "startTime": "2026-01-15T00:00:00Z",
                    "generation": 1049.0,
                },
            ]
        )

        result = build_decision_time_series(fuelhh, windfor, DEFAULT_CONFIG)

        assert len(result) == 2
        assert (result["forecast_mw"] == 900.0).all()
        assert (result["decision_publish_time"] == pd.Timestamp("2026-01-14T09:30:00Z")).all()
        assert result.loc[result["settlementPeriod"] == 1, "actual_mw"].item() == 1000.0
        assert result.loc[result["settlementPeriod"] == 2, "actual_mw"].item() == 1050.0

    def test_raises_when_a_day_has_no_eligible_forecast(self):
        fuelhh = make_fuelhh_df(
            [
                {
                    "settlementDate": "2026-01-15",
                    "settlementPeriod": 1,
                    "startTime": "2026-01-15T00:00:00Z",
                    "generation": 1000.0,
                },
            ]
        )
        windfor = make_windfor_df(
            [
                {
                    "publishTime": "2026-01-14T12:00:00Z",  # after cutoff only
                    "startTime": "2026-01-15T00:00:00Z",
                    "generation": 900.0,
                },
            ]
        )
        with pytest.raises(NoEligibleForecastError):
            build_decision_time_series(fuelhh, windfor, DEFAULT_CONFIG)
