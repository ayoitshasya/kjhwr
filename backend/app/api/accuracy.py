from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.schemas.responses import AccuracyResponse, MetricsBlock, QuantileSet, SlicedMetricsBlock
from app.services.accuracy_service import (
    DATA_COVERAGE_NOTE,
    actual_generation_decile,
    bucket_horizon,
    sliced_metrics,
    summary_metrics,
    with_errors,
    with_horizon_hours,
)
from app.services.comparison_service import get_comparison_series

router = APIRouter()


def _to_metrics_block(metrics: dict) -> MetricsBlock:
    return MetricsBlock(
        count=metrics["count"],
        mae_mw=metrics["mae_mw"],
        rmse_mw=metrics["rmse_mw"],
        bias_mw=metrics["bias_mw"],
        mae_pct_of_mean=metrics["mae_pct_of_mean"],
        mean_actual_mw=metrics["mean_actual_mw"],
        quantiles_mw=QuantileSet(**metrics["quantiles_mw"]),
    )


def _to_sliced_block(metrics: dict) -> SlicedMetricsBlock:
    return SlicedMetricsBlock(slice=metrics["slice"], **_to_metrics_block(metrics).model_dump())


@router.get("/accuracy", response_model=AccuracyResponse)
def get_accuracy(
    from_: date = Query(..., alias="from"),
    to: date = Query(...),
    confidence: float = Query(default=None, gt=0, lt=1),
) -> AccuracyResponse:
    if from_ > to:
        raise HTTPException(status_code=400, detail="'from' must not be after 'to'")
    confidence = confidence if confidence is not None else settings.default_confidence

    df = get_comparison_series(from_, to)
    if df.empty:
        raise HTTPException(
            status_code=404, detail="No comparison data available for the requested range"
        )

    df = with_horizon_hours(with_errors(df))
    df["horizon_bucket"] = bucket_horizon(df["horizon_hours"])
    df["actual_decile"] = actual_generation_decile(df["actual_mw"])

    overall = summary_metrics(df)
    safe_volume_quantile_mw = df["error_mw"].quantile(1 - confidence)

    return AccuracyResponse(
        date_from=from_.isoformat(),
        date_to=to.isoformat(),
        confidence=confidence,
        safe_volume_quantile_mw=float(safe_volume_quantile_mw),
        data_coverage_note=DATA_COVERAGE_NOTE,
        overall=_to_metrics_block(overall),
        by_settlement_period=[
            _to_sliced_block(m) for m in sliced_metrics(df, by="settlementPeriod")
        ],
        by_day=[_to_sliced_block(m) for m in sliced_metrics(df, by="settlementDate")],
        by_horizon_bucket=[_to_sliced_block(m) for m in sliced_metrics(df, by="horizon_bucket")],
        by_actual_decile=[_to_sliced_block(m) for m in sliced_metrics(df, by="actual_decile")],
    )
