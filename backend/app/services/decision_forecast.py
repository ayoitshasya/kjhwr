"""The decision-time forecast selection rule.

This is the core business rule the whole product hinges on: for a given delivery
settlement period, the only forecast the desk could actually have acted on is the
latest WINDFOR publication issued *before* gate closure (11:00 UK time, the day
before delivery). Everything here is a pure function of its inputs so the rule can be
unit-tested in isolation from the API and from pandas plumbing where possible.

Two deliberate design decisions, also called out in ARCHITECTURE.md:

1. The cutoff is computed per *delivery day*, not per settlement period. Gate closure
   happens once each morning for the whole next delivery day, so every settlement
   period within that day shares the same decision-time forecast run.
2. WINDFOR is hourly; settlement periods are half-hourly. The forecast value used for
   a settlement period is the hourly forecast for the clock hour containing that
   period's start time (broadcast/hold). See `floor_to_hour`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd


class NoEligibleForecastError(ValueError):
    """Raised when no WINDFOR publish exists before the decision-time cutoff."""


@dataclass(frozen=True)
class DecisionRuleConfig:
    cutoff_time: str = "11:00"
    cutoff_timezone: str = "Europe/London"
    days_before: int = 1


def decision_cutoff_utc(delivery_date: date, config: DecisionRuleConfig) -> datetime:
    """The gate-closure instant for a delivery day, in UTC.

    Computed by building the cutoff as a timezone-AWARE local datetime (not a naive
    datetime later assumed to be UTC), so the UK's BST/GMT offset is resolved correctly
    for whichever date is given — this deliberately does not hardcode a fixed UTC
    offset, even though the January 2026 scope only ever exercises GMT (UTC+0).
    """
    decision_date = delivery_date - timedelta(days=config.days_before)
    hour, minute = (int(part) for part in config.cutoff_time.split(":"))
    local_cutoff = datetime(
        decision_date.year,
        decision_date.month,
        decision_date.day,
        hour,
        minute,
        tzinfo=ZoneInfo(config.cutoff_timezone),
    )
    return local_cutoff.astimezone(ZoneInfo("UTC"))


def select_decision_publish_time(
    publish_times: pd.Series, cutoff_utc: datetime
) -> pd.Timestamp:
    """The latest WINDFOR publishTime strictly before the cutoff.

    Strictly-before (not inclusive): a forecast published exactly at 11:00:00 was not
    yet available when gate closure happened, so it must not be used.
    """
    cutoff_ts = pd.Timestamp(cutoff_utc)
    eligible = publish_times[publish_times < cutoff_ts]
    if eligible.empty:
        raise NoEligibleForecastError(
            f"No WINDFOR publish found before cutoff {cutoff_ts.isoformat()}"
        )
    return eligible.max()


def floor_to_hour(timestamp: pd.Series) -> pd.Series:
    """Map a half-hourly settlement-period start time to its containing clock hour."""
    return timestamp.dt.floor("h")


def build_decision_time_series(
    fuelhh_df: pd.DataFrame,
    windfor_df: pd.DataFrame,
    config: DecisionRuleConfig | None = None,
) -> pd.DataFrame:
    """Join actuals to their decision-time forecast, one row per settlement period.

    Returns columns: settlementDate, settlementPeriod, startTime, actual_mw,
    forecast_mw, decision_publish_time, cutoff_utc.

    Raises NoEligibleForecastError if any delivery day in fuelhh_df has no eligible
    forecast publish (surfaced to the caller rather than silently skipped or falling
    back to a later, information-leaking forecast).
    """
    config = config or DecisionRuleConfig()
    windfor_df = windfor_df.copy()
    windfor_df["floor_startTime"] = floor_to_hour(windfor_df["startTime"])

    rows = []
    for settlement_date, day_actuals in fuelhh_df.groupby("settlementDate"):
        delivery_date = date.fromisoformat(settlement_date)
        cutoff_utc = decision_cutoff_utc(delivery_date, config)
        decision_publish_time = select_decision_publish_time(
            windfor_df["publishTime"], cutoff_utc
        )

        run_curve = windfor_df[windfor_df["publishTime"] == decision_publish_time]
        hourly_lookup = run_curve.set_index("floor_startTime")["generation"]

        day_actuals = day_actuals.copy()
        day_actuals["floor_startTime"] = floor_to_hour(day_actuals["startTime"])
        day_actuals["forecast_mw"] = day_actuals["floor_startTime"].map(hourly_lookup)
        day_actuals["decision_publish_time"] = decision_publish_time
        day_actuals["cutoff_utc"] = pd.Timestamp(cutoff_utc)
        rows.append(day_actuals)

    result = pd.concat(rows, ignore_index=True)
    result = result.rename(columns={"generation": "actual_mw"})
    return result[
        [
            "settlementDate",
            "settlementPeriod",
            "startTime",
            "actual_mw",
            "forecast_mw",
            "decision_publish_time",
            "cutoff_utc",
        ]
    ].sort_values(["settlementDate", "settlementPeriod"], ignore_index=True)
