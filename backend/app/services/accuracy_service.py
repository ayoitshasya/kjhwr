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

KNOWN DATA CAVEAT - read before trusting "bias" at face value
---------------------------------------------------------------
error_mw (and therefore bias_mw) is persistently negative across every settlement
period and every actual-generation decile for January 2026 (roughly -700 to -2,800 MW,
overall -1,840 MW). This is dominantly a dataset coverage gap, not forecast skill:
FUELHH's WIND fuel type is built from Operational Metering of Balancing Mechanism
units - transmission-connected wind farms - and structurally excludes embedded/
unmetered wind generation. WINDFOR is NESO's national day-ahead forecast, which
approximates total system-wide GB wind (transmission + embedded).

This is now confirmed quantitatively, not just by elimination. NESO publishes its own
"Estimated Embedded Wind Generation" series (data.neso.energy, Historic Demand Data).
For January 2026, over the same 1,488 half-hourly periods as our data: FUELHH actual
total = 8,616 GWh; NESO's independent embedded-wind-actual total = 1,921 GWh; summed =
10,537 GWh. An independently reported January 2026 GB wind record of 10,600 GWh
(trade-press coverage of the month) is within 0.6% of that sum - i.e. FUELHH plus
NESO's own embedded-wind estimate reproduces the independent total almost exactly,
while FUELHH alone is only 81.3% of it. Our WINDFOR decision-time forecast total
(9,985 GWh) sits much closer to that combined total (-5.5%) than to FUELHH alone
(+15.9%), consistent with WINDFOR's scope already approximating the combined total
and modestly underforecasting it - ordinary day-ahead forecast error, not a second
scope mismatch. A join/timezone bug was ruled out separately: shifting the forecast by
up to +-2 hours relative to actuals does not materially change MAE or bias, which a
real alignment bug would. See README.md "Known data caveat" for the full investigation.

Caveat on the caveat: the -1,840 MW bias is smaller in magnitude than NESO's 2,582 MW
mean embedded-wind estimate for the month (ratio ~0.71) - same sign, same order of
magnitude, but not an exact 1:1. The coverage gap is the dominant driver of the bias;
the remaining ~700-900 MW is consistent with ordinary forecast error on top of it, not
fully attributable to coverage alone.

Practical consequence: safe_volume_mw stays correctly calibrated (it's an empirical
quantile of this exact error distribution, not something that assumes zero-mean error),
but bias_mw should not be read as "the forecaster overshoots by this many MW" - most of
it is a near-total-GB-wind forecast being compared against a partial-coverage actual.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

DEFAULT_QUANTILES: tuple[float, ...] = (0.1, 0.5, 0.9)

DATA_COVERAGE_NOTE = (
    "Bias is persistently negative (actual reads below forecast) across every slice. "
    "This is a known dataset coverage gap, confirmed quantitatively, not primarily "
    "forecast error: FUELHH WIND covers only Balancing-Mechanism-metered wind farms, "
    "while WINDFOR approximates total GB wind. For January 2026, FUELHH actual (8,616 "
    "GWh) plus NESO's own independent embedded-wind-generation estimate (1,921 GWh) "
    "sums to 10,537 GWh - within 0.6% of the independently reported 10,600 GWh GB wind "
    "total for the month - while FUELHH alone is only 81.3% of it. The coverage gap is "
    "the dominant driver of the bias, though not the sole one: a residual ~700-900 MW "
    "looks like ordinary forecast error layered on top. A join/timezone bug was ruled "
    "out separately: shifting the forecast +-2 hours does not reduce error. See "
    "README.md for the full investigation."
)


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
