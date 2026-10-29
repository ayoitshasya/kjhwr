"""Pydantic response models. Every API endpoint returns one of these - never a raw dict."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class ForecastPeriod(BaseModel):
    settlementPeriod: int
    startTime: datetime
    forecast_mw: float
    lower_band_mw: float
    upper_band_mw: float


class ForecastResponse(BaseModel):
    date: str
    confidence: float
    decision_publish_time: datetime
    cutoff_utc: datetime
    periods: list[ForecastPeriod]
    total_forecast_mwh: float
    total_safe_volume_mwh: float
    implied_buffer_mwh: float = Field(
        description="total_forecast_mwh - total_safe_volume_mwh, the risk buffer size"
    )


class ActualPeriod(BaseModel):
    settlementDate: str
    settlementPeriod: int
    startTime: datetime
    actual_mw: float


class ActualsResponse(BaseModel):
    date_from: str
    date_to: str
    periods: list[ActualPeriod]


class ComparisonPeriod(BaseModel):
    settlementDate: str
    settlementPeriod: int
    startTime: datetime
    actual_mw: float
    forecast_mw: float
    error_mw: float
    decision_publish_time: datetime
    horizon_hours: float


class ComparisonResponse(BaseModel):
    date_from: str
    date_to: str
    periods: list[ComparisonPeriod]


class QuantileSet(BaseModel):
    p10: float | None = None
    p50: float | None = None
    p90: float | None = None


class MetricsBlock(BaseModel):
    count: int
    mae_mw: float | None
    rmse_mw: float | None
    bias_mw: float | None
    mae_pct_of_mean: float | None
    mean_actual_mw: float | None
    quantiles_mw: QuantileSet


class SlicedMetricsBlock(MetricsBlock):
    slice: str | int | float


class AccuracyResponse(BaseModel):
    date_from: str
    date_to: str
    confidence: float
    safe_volume_quantile_mw: float = Field(
        description="quantile(error_mw, 1 - confidence) used to derive safe volume"
    )
    overall: MetricsBlock
    by_settlement_period: list[SlicedMetricsBlock]
    by_day: list[SlicedMetricsBlock]
    by_horizon_bucket: list[SlicedMetricsBlock]
    by_actual_decile: list[SlicedMetricsBlock]
