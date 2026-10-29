from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.elexon import cache
from app.schemas.responses import ForecastPeriod, ForecastResponse
from app.services.accuracy_service import with_errors
from app.services.comparison_service import get_comparison_series
from app.services.decision_forecast import (
    DecisionRuleConfig,
    NoEligibleForecastError,
    build_decision_time_series,
)

router = APIRouter()

_SETTLEMENT_HOURS = 0.5  # half-hourly settlement periods -> MWh = MW * 0.5h
_BAND_LOWER_QUANTILE = 0.1
_BAND_UPPER_QUANTILE = 0.9


def _error_quantile(quantile: float) -> float:
    """Empirical error quantile over the full cached comparison series.

    The shaded confidence band on the Decision view uses the fixed P10/P90 empirical
    quantiles (the distribution the Accuracy view also reports), independent of the
    separate single-number confidence level the desk picks for the headline safe
    volume. See ARCHITECTURE.md for why these are deliberately decoupled.
    """
    fuelhh = cache.load_fuelhh()
    full_from = date.fromisoformat(fuelhh["settlementDate"].min())
    full_to = date.fromisoformat(fuelhh["settlementDate"].max())
    full_comparison = with_errors(get_comparison_series(full_from, full_to))
    return float(full_comparison["error_mw"].quantile(quantile))


@router.get("/forecast", response_model=ForecastResponse)
def get_forecast(
    date_: date = Query(..., alias="date"),
    confidence: float = Query(default=None, gt=0, lt=1),
) -> ForecastResponse:
    confidence = confidence if confidence is not None else settings.default_confidence

    fuelhh = cache.load_fuelhh()
    day_rows = fuelhh[fuelhh["settlementDate"] == date_.isoformat()]
    if day_rows.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No settlement period structure cached for {date_.isoformat()}",
        )

    windfor = cache.load_windfor()
    try:
        decision_series = build_decision_time_series(day_rows, windfor, DecisionRuleConfig())
    except NoEligibleForecastError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    safe_volume_quantile = _error_quantile(1 - confidence)
    lower_quantile = _error_quantile(_BAND_LOWER_QUANTILE)
    upper_quantile = _error_quantile(_BAND_UPPER_QUANTILE)

    decision_series = decision_series.sort_values("settlementPeriod")
    periods = [
        ForecastPeriod(
            settlementPeriod=row.settlementPeriod,
            startTime=row.startTime,
            forecast_mw=row.forecast_mw,
            lower_band_mw=row.forecast_mw + lower_quantile,
            upper_band_mw=row.forecast_mw + upper_quantile,
        )
        for row in decision_series.itertuples()
    ]

    total_forecast_mwh = float(decision_series["forecast_mw"].sum() * _SETTLEMENT_HOURS)
    total_safe_volume_mwh = float(
        (decision_series["forecast_mw"] + safe_volume_quantile).sum() * _SETTLEMENT_HOURS
    )

    first_row = decision_series.iloc[0]
    return ForecastResponse(
        date=date_.isoformat(),
        confidence=confidence,
        decision_publish_time=first_row["decision_publish_time"],
        cutoff_utc=first_row["cutoff_utc"],
        periods=periods,
        total_forecast_mwh=total_forecast_mwh,
        total_safe_volume_mwh=total_safe_volume_mwh,
        implied_buffer_mwh=total_forecast_mwh - total_safe_volume_mwh,
    )
