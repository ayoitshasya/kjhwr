"""Re-fetch Elexon data and overwrite the committed parquet snapshots.

Run manually when the cached data needs to be regenerated:

    python scripts/refresh_data.py

The window fetched is wider than the January 2026 analysis scope on both ends:
  - Back to mid-December 2025 so that January 1st's decision-time forecast (whose
    gate closure falls on Dec 31st) and the longest forecast horizons are covered.
  - Forward to the end of January 2026.
"""

import asyncio
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.elexon.cache import refresh_fuelhh, refresh_windfor  # noqa: E402

FETCH_FROM_DATE = date(2025, 12, 15)
FETCH_TO_DATE = date(2026, 1, 31)


async def main() -> None:
    print(f"Fetching FUELHH WIND actuals {FETCH_FROM_DATE} -> {FETCH_TO_DATE} ...")
    fuelhh_df = await refresh_fuelhh(FETCH_FROM_DATE, FETCH_TO_DATE)
    print(f"  {len(fuelhh_df)} rows written.")

    dt_from = datetime.combine(FETCH_FROM_DATE, datetime.min.time())
    dt_to = datetime.combine(FETCH_TO_DATE, datetime.max.time())
    print(f"Fetching WINDFOR forecasts {dt_from} -> {dt_to} ...")
    windfor_df = await refresh_windfor(dt_from, dt_to)
    print(f"  {len(windfor_df)} rows written.")


if __name__ == "__main__":
    asyncio.run(main())
