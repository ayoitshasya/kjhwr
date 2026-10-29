"""Builds the forecast-vs-actual comparison series over a date range."""

from __future__ import annotations

from datetime import date

import pandas as pd

from app.elexon import cache
from app.services.decision_forecast import DecisionRuleConfig, build_decision_time_series


def get_comparison_series(
    date_from: date, date_to: date, config: DecisionRuleConfig | None = None
) -> pd.DataFrame:
    """Decision-time forecast vs actual, one row per settlement period, for a date range."""
    fuelhh_df = cache.load_fuelhh()
    windfor_df = cache.load_windfor()

    mask = (fuelhh_df["settlementDate"] >= date_from.isoformat()) & (
        fuelhh_df["settlementDate"] <= date_to.isoformat()
    )
    fuelhh_in_range = fuelhh_df[mask]
    if fuelhh_in_range.empty:
        return pd.DataFrame(
            columns=[
                "settlementDate",
                "settlementPeriod",
                "startTime",
                "actual_mw",
                "forecast_mw",
                "decision_publish_time",
                "cutoff_utc",
            ]
        )

    return build_decision_time_series(fuelhh_in_range, windfor_df, config)
