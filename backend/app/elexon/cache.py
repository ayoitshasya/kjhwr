"""Local CSV cache for Elexon data.

The service layer always reads through this module and never calls Elexon directly.
This keeps the running app offline-first: the committed snapshots mean the demo works
with no network access and never fails live. `scripts/refresh_data.py` is the only
thing that writes these files.

CSV rather than parquet deliberately: parquet needs pyarrow, whose wheel is tens of MB
and made the backend Docker build fragile on a slow connection, for a dataset small
enough (a few MB) that the format makes no practical difference here.
"""

from __future__ import annotations

from datetime import date, datetime

import pandas as pd

from app.config import FUELHH_CACHE_FILE, WINDFOR_CACHE_FILE
from app.elexon.client import ElexonClient


def fuelhh_columns() -> list[str]:
    return ["publishTime", "startTime", "settlementDate", "settlementPeriod", "generation"]


def windfor_columns() -> list[str]:
    return ["publishTime", "startTime", "generation"]


def load_fuelhh() -> pd.DataFrame:
    if not FUELHH_CACHE_FILE.exists():
        raise FileNotFoundError(
            f"No cached FUELHH data at {FUELHH_CACHE_FILE}. Run scripts/refresh_data.py."
        )
    return pd.read_csv(
        FUELHH_CACHE_FILE,
        dtype={"settlementDate": str, "settlementPeriod": int, "generation": float},
        parse_dates=["publishTime", "startTime"],
    )


def load_windfor() -> pd.DataFrame:
    if not WINDFOR_CACHE_FILE.exists():
        raise FileNotFoundError(
            f"No cached WINDFOR data at {WINDFOR_CACHE_FILE}. Run scripts/refresh_data.py."
        )
    return pd.read_csv(
        WINDFOR_CACHE_FILE,
        dtype={"generation": float},
        parse_dates=["publishTime", "startTime"],
    )


async def refresh_fuelhh(
    date_from: date, date_to: date, client: ElexonClient | None = None
) -> pd.DataFrame:
    client = client or ElexonClient()
    rows = await client.fetch_fuelhh_wind(date_from, date_to)
    df = pd.DataFrame([row.model_dump() for row in rows])[fuelhh_columns()]
    df = df.sort_values(["startTime"]).drop_duplicates(subset=["startTime"], keep="last")
    FUELHH_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(FUELHH_CACHE_FILE, index=False)
    return df


async def refresh_windfor(
    dt_from: datetime, dt_to: datetime, client: ElexonClient | None = None
) -> pd.DataFrame:
    client = client or ElexonClient()
    rows = await client.fetch_windfor(dt_from, dt_to)
    df = pd.DataFrame([row.model_dump() for row in rows])[windfor_columns()]
    df = df.sort_values(["publishTime", "startTime"]).drop_duplicates(
        subset=["publishTime", "startTime"], keep="last"
    )
    WINDFOR_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(WINDFOR_CACHE_FILE, index=False)
    return df
