"""Async client for the Elexon Insights API (no API key required).

Confirmed empirically (no reachable OpenAPI spec at the documented URLs):
  - FUELHH/stream takes settlementDateFrom / settlementDateTo (YYYY-MM-DD) and fuelType.
  - WINDFOR/stream takes publishDateTimeFrom / publishDateTimeTo (ISO datetime, UTC).
Full-month ranges returned successfully with no pagination/truncation observed, but we
still fetch in bounded weekly chunks: it's kinder to a public, unauthenticated API and
guards against an undocumented limit silently truncating a large single request.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import ELEXON_BASE_URL
from app.elexon.raw_models import FuelHHRow, WindForRow

_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
_CHUNK_DAYS = 7

_retryable = retry(
    retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(4),
    reraise=True,
)


def _date_chunks(start: date, end: date, chunk_days: int) -> list[tuple[date, date]]:
    """Split [start, end] inclusive into bounded chunks."""
    chunks = []
    cur = start
    while cur <= end:
        chunk_end = min(cur + timedelta(days=chunk_days - 1), end)
        chunks.append((cur, chunk_end))
        cur = chunk_end + timedelta(days=1)
    return chunks


class ElexonClient:
    def __init__(self, base_url: str = ELEXON_BASE_URL) -> None:
        self._base_url = base_url

    @_retryable
    async def _get(self, client: httpx.AsyncClient, path: str, params: dict) -> list[dict]:
        response = await client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    async def fetch_fuelhh_wind(self, date_from: date, date_to: date) -> list[FuelHHRow]:
        """Fetch half-hourly WIND outturn generation for [date_from, date_to] inclusive."""
        rows: list[FuelHHRow] = []
        async with httpx.AsyncClient(base_url=self._base_url, timeout=_TIMEOUT) as client:
            for chunk_start, chunk_end in _date_chunks(date_from, date_to, _CHUNK_DAYS):
                payload = await self._get(
                    client,
                    "/datasets/FUELHH/stream",
                    {
                        "settlementDateFrom": chunk_start.isoformat(),
                        "settlementDateTo": chunk_end.isoformat(),
                        "fuelType": "WIND",
                    },
                )
                rows.extend(FuelHHRow.model_validate(row) for row in payload)
        return rows

    async def fetch_windfor(self, dt_from: datetime, dt_to: datetime) -> list[WindForRow]:
        """Fetch hourly national wind forecast publishes for [dt_from, dt_to] inclusive."""
        rows: list[WindForRow] = []
        async with httpx.AsyncClient(base_url=self._base_url, timeout=_TIMEOUT) as client:
            for chunk_start, chunk_end in _date_chunks(dt_from.date(), dt_to.date(), _CHUNK_DAYS):
                chunk_from = max(dt_from, datetime.combine(chunk_start, datetime.min.time()))
                chunk_to = min(dt_to, datetime.combine(chunk_end, datetime.max.time()))
                payload = await self._get(
                    client,
                    "/datasets/WINDFOR/stream",
                    {
                        "publishDateTimeFrom": chunk_from.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "publishDateTimeTo": chunk_to.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    },
                )
                rows.extend(WindForRow.model_validate(row) for row in payload)
        return rows
