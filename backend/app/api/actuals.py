from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.elexon import cache
from app.schemas.responses import ActualPeriod, ActualsResponse

router = APIRouter()


@router.get("/actuals", response_model=ActualsResponse)
def get_actuals(
    from_: date = Query(..., alias="from"),
    to: date = Query(...),
) -> ActualsResponse:
    if from_ > to:
        raise HTTPException(status_code=400, detail="'from' must not be after 'to'")

    df = cache.load_fuelhh()
    mask = (df["settlementDate"] >= from_.isoformat()) & (df["settlementDate"] <= to.isoformat())
    df = df[mask].sort_values(["settlementDate", "settlementPeriod"])

    periods = [
        ActualPeriod(
            settlementDate=row.settlementDate,
            settlementPeriod=row.settlementPeriod,
            startTime=row.startTime,
            actual_mw=row.generation,
        )
        for row in df.itertuples()
    ]
    return ActualsResponse(date_from=from_.isoformat(), date_to=to.isoformat(), periods=periods)
