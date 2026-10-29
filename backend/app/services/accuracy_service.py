"""Forecast error metrics over a decision-time comparison series.

Error convention: error_mw = actual_mw - forecast_mw.
  - Positive error: the desk under-forecast (actual wind came in higher than expected).
  - Negative error: the desk over-forecast (actual wind fell short) - this is the side
    that matters for a buyer sizing a risk buffer against residual demand.

Safe volume at confidence level c: forecast_mw + quantile(error_mw, 1 - c).
quantile(error_mw, 0.10) is typically negative, so adding it reduces the forecast -
this is the "forecast minus the error quantile" the brief describes, expressed as an
addition of a (usually negative) quantile rather than a subtraction of its magnitude,
so the same formula works unchanged if the error distribution is ever skewed positive.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

DEFAULT_QUANTILES: tuple[float, ...] = (0.1, 0.5, 0.9)


def with_errors(comparison_df: pd.DataFrame) -> pd.DataFrame:
    df = comparison_df.copy()
    df["error_mw"] = df["actual_mw"] - df["forecast_mw"]
    return df


def with_horizon_hours(comparison_df: pd.DataFrame) -> pd.DataFrame:
    df = comparison_df.copy()
    df["horizon_hours"] = (
        df["startTime"] - df["decision_publish_time"]
    ).dt.total_seconds() / 3600
    return df


def bucket_horizon(horizon_hours: pd.Series, bin_size_hours: int = 6) -> pd.Series:
    """Bin forecast horizon into fixed-width hour buckets, labelled by the bucket start."""
    return (np.floor(horizon_hours / bin_size_hours) * bin_size_hours).astype(int)


def actual_generation_decile(actual_mw: pd.Series) -> pd.Series:
    """1-10 decile of actual generation, 1 = lowest-output decile."""
    return pd.qcut(actual_mw, 10, labels=False, duplicates="drop") + 1


def summary_metrics(df: pd.DataFrame, quantiles: tuple[float, ...] = DEFAULT_QUANTILES) -> dict:
    """Headline error metrics for a (possibly sliced) set of comparison rows."""
    if df.empty:
        return {
            "count": 0,
            "mae_mw": None,
            "rmse_mw": None,
            "bias_mw": None,
            "mae_pct_of_mean": None,
            "mean_actual_mw": None,
            "quantiles_mw": {},
        }
    error = df["error_mw"]
    mean_actual = df["actual_mw"].mean()
    mae = error.abs().mean()
    rmse = float(np.sqrt((error**2).mean()))
    bias = error.mean()
    mae_pct = (mae / mean_actual * 100) if mean_actual else None
    return {
        "count": int(len(df)),
        "mae_mw": float(mae),
        "rmse_mw": rmse,
        "bias_mw": float(bias),
        "mae_pct_of_mean": float(mae_pct) if mae_pct is not None else None,
        "mean_actual_mw": float(mean_actual),
        "quantiles_mw": {
            f"p{int(round(q * 100))}": float(error.quantile(q)) for q in quantiles
        },
    }


def sliced_metrics(
    df: pd.DataFrame, by: str, quantiles: tuple[float, ...] = DEFAULT_QUANTILES
) -> list[dict]:
    """summary_metrics grouped by an arbitrary column, sorted by slice key."""
    out = []
    for key, group in df.groupby(by):
        metrics = summary_metrics(group, quantiles)
        metrics["slice"] = key.item() if hasattr(key, "item") else key
        out.append(metrics)
    return sorted(out, key=lambda m: m["slice"])


def safe_volume_mw(forecast_mw: float, error_quantile_value: float) -> float:
    """The MW the desk can count on at the confidence level implied by the quantile."""
    return forecast_mw + error_quantile_value
