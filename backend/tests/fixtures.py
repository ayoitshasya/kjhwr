"""Small, hand-built fixtures for the analysis engine tests.

These are deliberately tiny and fully traceable by hand - the point of this test suite
is to prove the decision-time rule and the metric maths against numbers a reviewer can
re-derive on paper, not to exercise pandas against itself.
"""

from __future__ import annotations

import pandas as pd


def make_fuelhh_df(rows: list[dict]) -> pd.DataFrame:
    """rows: [{"settlementDate": "2026-01-02", "settlementPeriod": 1,
               "startTime": "2026-01-02T00:00:00Z", "generation": 1000.0}, ...]"""
    df = pd.DataFrame(rows)
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    return df


def make_windfor_df(rows: list[dict]) -> pd.DataFrame:
    """rows: [{"publishTime": "2026-01-01T10:30:00Z",
               "startTime": "2026-01-02T00:00:00Z", "generation": 950.0}, ...]"""
    df = pd.DataFrame(rows)
    df["publishTime"] = pd.to_datetime(df["publishTime"], utc=True)
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    return df
