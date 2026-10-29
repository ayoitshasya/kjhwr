"""Re-fetch Elexon data and overwrite the committed parquet snapshots.

Run manually when the cached data needs to be regenerated:

    python scripts/refresh_data.py

FUELHH actuals are fetched for exactly the January 2026 analysis scope - no more,
since the brief scopes "decisions for January 2026" and any extra cached actual days
would need their own decision-time forecast lookback too (see WINDFOR note below).

WINDFOR forecasts are fetched from well before the scope starts, back to mid-December
2025, purely as lookback buffer: January 1st's decision-time forecast is selected from
whatever WINDFOR runs were published before 11:00 UK time on December 31st, so that
publish (and the runs around it) must already be in the cache.
"""

import asyncio
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.elexon.cache import refresh_fuelhh, refresh_windfor  # noqa: E402

FUELHH_FROM_DATE = date(2026, 1, 1)
FUELHH_TO_DATE = date(2026, 1, 31)
WINDFOR_FROM_DATE = date(2025, 12, 15)
WINDFOR_TO_DATE = date(2026, 1, 31)


async def main() -> None:
    print(f"Fetching FUELHH WIND actuals {FUELHH_FROM_DATE} -> {FUELHH_TO_DATE} ...")
    fuelhh_df = await refresh_fuelhh(FUELHH_FROM_DATE, FUELHH_TO_DATE)
    print(f"  {len(fuelhh_df)} rows written.")

    dt_from = datetime.combine(WINDFOR_FROM_DATE, datetime.min.time())
    dt_to = datetime.combine(WINDFOR_TO_DATE, datetime.max.time())
    print(f"Fetching WINDFOR forecasts {dt_from} -> {dt_to} ...")
    windfor_df = await refresh_windfor(dt_from, dt_to)
    print(f"  {len(windfor_df)} rows written.")


if __name__ == "__main__":
    asyncio.run(main())
