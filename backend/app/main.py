from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import accuracy, actuals, comparison, forecast, health
from app.config import settings
from app.services.decision_forecast import NoEligibleForecastError

app = FastAPI(
    title="GB Wind Day-Ahead Purchasing Desk API",
    description=(
        "Decision-time wind forecast and forecast-error analysis for a UK day-ahead "
        "power purchasing desk, scoped to GB national wind and January 2026."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.exception_handler(NoEligibleForecastError)
async def no_eligible_forecast_handler(_request, exc: NoEligibleForecastError) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"error": {"code": "no_eligible_forecast", "message": str(exc)}},
    )


@app.exception_handler(FileNotFoundError)
async def missing_cache_handler(_request, exc: FileNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"error": {"code": "cache_unavailable", "message": str(exc)}},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "http_error", "message": str(exc.detail)}},
    )


app.include_router(health.router, prefix="/api")
app.include_router(forecast.router, prefix="/api")
app.include_router(actuals.router, prefix="/api")
app.include_router(comparison.router, prefix="/api")
app.include_router(accuracy.router, prefix="/api")
