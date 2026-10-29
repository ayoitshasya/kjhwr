from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.schemas.responses import ComparisonPeriod, ComparisonResponse
from app.services.accuracy_service import with_errors, with_horizon_hours
from app.services.comparison_service import get_comparison_series

router = APIRouter()


@router.get("/comparison", response_model=ComparisonResponse)
def get_comparison(
    from_: date = Query(..., alias="from"),
    to: date = Query(...),
) -> ComparisonResponse:
    if from_ > to:
        raise HTTPException(status_code=400, detail="'from' must not be after 'to'")

    df = get_comparison_series(from_, to)
    if df.empty:
        return ComparisonResponse(date_from=from_.isoformat(), date_to=to.isoformat(), periods=[])

    df = with_horizon_hours(with_errors(df))

    periods = [
        ComparisonPeriod(
            settlementDate=row.settlementDate,
            settlementPeriod=row.settlementPeriod,
            startTime=row.startTime,
            actual_mw=row.actual_mw,
            forecast_mw=row.forecast_mw,
            error_mw=row.error_mw,
            decision_publish_time=row.decision_publish_time,
            horizon_hours=row.horizon_hours,
        )
        for row in df.itertuples()
    ]
    return ComparisonResponse(date_from=from_.isoformat(), date_to=to.isoformat(), periods=periods)
