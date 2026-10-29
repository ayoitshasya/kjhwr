"""Pydantic models for the raw Elexon Insights API rows.

Field names and shapes were confirmed by live test calls against
https://data.elexon.co.uk/bmrs/api/v1 (no committed OpenAPI spec was reachable at the
documented URLs — see ARCHITECTURE.md for the investigation).
"""

from datetime import datetime

from pydantic import BaseModel


class FuelHHRow(BaseModel):
    """One row from /datasets/FUELHH/stream — half-hourly outturn generation by fuel type."""

    dataset: str
    publishTime: datetime
    startTime: datetime
    settlementDate: str
    settlementPeriod: int
    fuelType: str
    generation: float


class WindForRow(BaseModel):
    """One row from /datasets/WINDFOR/stream — hourly national wind forecast.

    Unlike FUELHH, WINDFOR carries no settlementDate/settlementPeriod — only a
    timestamp. Resolution is hourly, not half-hourly.
    """

    dataset: str
    publishTime: datetime
    startTime: datetime
    generation: float
