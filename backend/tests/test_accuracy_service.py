import math

import pandas as pd
import pytest

from app.services.accuracy_service import (
    actual_generation_decile,
    bucket_horizon,
    safe_volume_mw,
    sliced_metrics,
    summary_metrics,
    with_errors,
)


def _comparison_df():
    # forecast is constant at 100; actual varies -10/-5/0/+5/+10 around it.
    # error = actual - forecast = [-10, -5, 0, 5, 10]
    df = pd.DataFrame(
        {
            "actual_mw": [90.0, 95.0, 100.0, 105.0, 110.0],
            "forecast_mw": [100.0, 100.0, 100.0, 100.0, 100.0],
        }
    )
    return with_errors(df)


class TestSummaryMetrics:
    def test_hand_computed_metrics(self):
        df = _comparison_df()
        metrics = summary_metrics(df, quantiles=(0.1, 0.5, 0.9))

        assert metrics["count"] == 5
        # MAE = mean(|[-10,-5,0,5,10]|) = (10+5+0+5+10)/5 = 6
        assert metrics["mae_mw"] == pytest.approx(6.0)
        # RMSE = sqrt(mean([100,25,0,25,100])) = sqrt(50)
        assert metrics["rmse_mw"] == pytest.approx(math.sqrt(50))
        # bias = mean(error) = 0
        assert metrics["bias_mw"] == pytest.approx(0.0)
        # mean actual = 100 -> MAE% = 6/100*100 = 6%
        assert metrics["mae_pct_of_mean"] == pytest.approx(6.0)
        # pandas linear-interpolation quantiles of sorted [-10,-5,0,5,10]:
        # p10 at position (n-1)*0.1=0.4 -> -10 + 0.4*5 = -8
        # p50 at position 2 -> 0
        # p90 at position 3.6 -> 5 + 0.6*5 = 8
        assert metrics["quantiles_mw"]["p10"] == pytest.approx(-8.0)
        assert metrics["quantiles_mw"]["p50"] == pytest.approx(0.0)
        assert metrics["quantiles_mw"]["p90"] == pytest.approx(8.0)

    def test_empty_slice_returns_nones_not_nan_or_crash(self):
        empty = _comparison_df().iloc[0:0]
        metrics = summary_metrics(empty)
        assert metrics["count"] == 0
        assert metrics["mae_mw"] is None


class TestSlicedMetrics:
    def test_groups_and_sorts_by_slice_key(self):
        df = _comparison_df()
        df["bucket"] = ["a", "a", "b", "b", "b"]
        sliced = sliced_metrics(df, by="bucket")

        assert [s["slice"] for s in sliced] == ["a", "b"]
        # group "a": actual=[90,95], forecast=100 -> error=[-10,-5] -> MAE=7.5
        assert sliced[0]["mae_mw"] == pytest.approx(7.5)
        assert sliced[0]["count"] == 2
        # group "b": actual=[100,105,110], forecast=100 -> error=[0,5,10] -> MAE=5
        assert sliced[1]["mae_mw"] == pytest.approx(5.0)
        assert sliced[1]["count"] == 3


class TestSafeVolume:
    def test_adds_quantile_to_forecast(self):
        # forecast=100, p10 error quantile=-8 -> safe volume = 92
        assert safe_volume_mw(forecast_mw=100.0, error_quantile_value=-8.0) == pytest.approx(92.0)


class TestBucketHorizon:
    def test_bins_into_fixed_width_buckets_labelled_by_start(self):
        hours = pd.Series([0.0, 3.9, 6.0, 13.5, 23.9])
        buckets = bucket_horizon(hours, bin_size_hours=6)
        assert list(buckets) == [0, 0, 6, 12, 18]


class TestActualGenerationDecile:
    def test_lowest_values_land_in_decile_1(self):
        # 10 evenly spaced values -> each its own decile, ascending.
        values = pd.Series(range(10))
        deciles = actual_generation_decile(values)
        assert deciles.iloc[0] == 1
        assert deciles.iloc[-1] == 10
