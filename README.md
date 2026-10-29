# GB Wind Day-Ahead Purchasing Desk

A decision-support tool for a UK day-ahead power purchasing desk: how much wind
generation to count on for each January 2026 delivery day, how big a risk buffer to
hold against forecast error, and how good the forecast actually is. Built on Elexon's
public Insights API (FUELHH half-hourly wind outturn, WINDFOR wind forecast) — no API
key required.

**Live demo:** _(placeholder — add the deployed frontend/backend URLs here)_

## Directory map

```
backend/
  app/
    main.py                  FastAPI app: CORS, router registration, error handlers
    config.py                 Settings — cutoff time/tz, cache dir, default confidence
    api/
      health.py               GET /api/health
      forecast.py              GET /api/forecast
      actuals.py               GET /api/actuals
      comparison.py            GET /api/comparison
      accuracy.py              GET /api/accuracy
    elexon/
      client.py                Async httpx client for the Elexon Insights API
      raw_models.py             Pydantic models for raw FUELHH/WINDFOR rows
      cache.py                  CSV cache: load/fetch-if-missing/save
    services/
      decision_forecast.py      The decision-time forecast selection rule
      comparison_service.py     Joins forecast + actual into one comparison series
      accuracy_service.py       Error metrics, slices, quantiles, data-coverage note
    schemas/
      responses.py              Pydantic response models for every endpoint
    data/
      fuelhh_wind.csv            Committed Jan 2026 WIND actuals snapshot
      windfor.csv                 Committed wind forecast snapshot (with lookback buffer)
  scripts/
    refresh_data.py             Re-fetches from Elexon, overwrites the CSV snapshots
  tests/
    test_decision_forecast.py   Selection rule + timezone edge cases
    test_accuracy_service.py    Metrics vs hand-computed fixtures
    test_api.py                 Endpoint contract tests (TestClient, real snapshot)
  pyproject.toml, requirements*.txt, requirements.lock, Dockerfile

frontend/
  src/
    api/                       Typed fetch client (client.ts) + TanStack Query hooks
    components/                Charts, metrics table, "how to read this" panels, etc.
    pages/
      DecisionView.tsx          Date picker, forecast curve, safe volume, risk buffer
      AccuracyView.tsx          Forecast-vs-actual, error metrics, slice tables
    App.tsx, main.tsx
  Dockerfile, nginx.conf, vite.config.ts, package.json

docker-compose.yml             Backend + frontend, backend healthcheck gates frontend
.env.example                   CORS_ORIGINS, DEFAULT_CONFIDENCE, VITE_API_BASE_URL
ARCHITECTURE.md                 Data flow, diagram, design decisions and alternatives
DEMO_SCRIPT.md                  Two-part video script
```

## Running it

### With Docker (recommended — no local Python/Node needed)

```bash
cp .env.example .env     # optional, defaults work for local use
docker compose up --build
```

- Backend: http://localhost:8000 (docs at `/docs`)
- Frontend: http://localhost:8080

The backend reads only from the committed CSV snapshots in `backend/app/data/` — it
never calls Elexon live, so the demo works offline and never fails on a network issue.

### Without Docker

Backend:

```bash
cd backend
python -m venv .venv && . .venv/Scripts/activate   # or source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

Set `VITE_API_BASE_URL` in `frontend/.env` if the backend isn't on `localhost:8000`,
and add the frontend's origin to `CORS_ORIGINS` in `backend/.env` if it isn't
`5173`/`8080`.

### Tests and lint

```bash
cd backend && pytest && ruff check .
cd frontend && npm run build && npm run lint   # tsc -b (typecheck) + build, then oxlint
```

### Refreshing the data snapshot

`backend/scripts/refresh_data.py` re-fetches FUELHH (January 2026) and WINDFOR (from
Dec 15 2025, for lookback) from the live Elexon API and overwrites the committed CSVs.
Not needed to run the app — only to pull newer data.

## The decision-time forecast rule

The desk can only act on the forecast it actually had in hand at the moment it had to
commit to a volume. For a delivery day, that moment — **gate closure** — is **11:00 UK
time on the day before delivery**. The rule:

1. Take every WINDFOR forecast publish for the relevant window.
2. Keep only the ones published **strictly before** 11:00 UK time the day before
   delivery (a publish landing exactly at 11:00 wasn't available yet).
3. Use the **latest** of those — it's the most information the desk could have had.
4. That one forecast run covers the whole delivery day; it isn't re-picked per
   settlement period, because gate closure happens once each morning, not 48 times.

WINDFOR publishes hourly forecasts; settlement periods are half-hourly. Each
half-hour's forecast value is the hourly forecast for the clock hour containing that
period's start (broadcast/hold — e.g. periods covering 14:00–14:30 and 14:30–15:00
both get the 14:00 hourly value), not an interpolation between hours. See
`backend/app/services/decision_forecast.py` and `ARCHITECTURE.md` for why.

The time comparison is timezone-aware (`zoneinfo("Europe/London")`), not a hardcoded
UTC offset, so the rule stays correct outside the GMT months even though this
dataset's January scope never exercises BST.

## Metrics

Error convention: **`error_mw = actual_mw − forecast_mw`**. Negative means actual
generation came in below forecast — the side that matters for a buyer who sized a
purchase on the forecast.

- **MAE** (mean absolute error) — typical size of the error, in MW.
- **RMSE** (root mean squared error) — like MAE but penalises large misses more.
- **Bias** — mean error. Systematic over/under-forecasting, not error size.
- **P10 / P50 / P90** — 10th/50th/90th percentile of the error distribution.
- **Safe volume** at confidence `c`: `forecast_mw + quantile(error_mw, 1 − c)`. At 90%
  confidence this adds the (usually negative) P10 of past errors to the forecast,
  giving a volume actual generation has met or exceeded 90% of the time historically.
- **Risk buffer**: `forecast_mw − safe_volume_mw` — the extra generation the desk
  should be ready to buy to cover the downside.

The Decision view's confidence band uses the *whole month's* error quantiles as a
constant-width band, rather than per-horizon or per-settlement-period quantiles — see
ARCHITECTURE.md for why (one month of data is too little to slice further without the
band becoming noisy).

## Known data caveat: why "bias" reads strongly negative

Every slice of the accuracy metrics — every settlement period, every day, every
actual-generation decile — shows a negative bias (actual below forecast), averaging
**-1,840 MW** over January 2026. Before trusting that as "the forecast overshoots,"
this was investigated rather than assumed:

| Check | Result |
|---|---|
| Bias by actual-generation decile | Not flat in MW, not cleanly proportional either — ranges -677 MW to -2,827 MW (-8.2% to -52.6% of that decile's mean actual) |
| MAE under forecast time-shift (±1, ±2, ±4 settlement periods) | No shift reduces error (2,048–2,295 MW across shifts vs. 2,126 MW unshifted); bias stays -1,800 to -1,856 MW throughout — rules out a join/timezone/alignment bug |
| Independent cross-check | FUELHH actual (8,616 GWh) + NESO's own published "Estimated Embedded Wind Generation" for Jan 2026 (1,921 GWh) = 10,537 GWh — **within 0.6%** of an independently reported Jan 2026 GB wind record of 10,600 GWh. FUELHH alone is only 81.3% of it |
| WINDFOR vs. the combined total | WINDFOR's decision-time forecast total (9,985 GWh) is 5.5% below the FUELHH+embedded combined total, vs. 15.9% above FUELHH alone — consistent with WINDFOR approximating the combined (not FUELHH-only) scope |

**Conclusion**: FUELHH's `WIND` fuel type is built from Operational Metering of
Balancing Mechanism units — transmission-connected wind farms — and structurally
excludes embedded/unmetered wind generation. WINDFOR approximates total GB wind
(transmission + embedded). This is a genuine dataset scope difference, confirmed
quantitatively against NESO's own independent embedded-wind series, and it is the
**dominant** driver of the bias.

It is not the *entire* story: the observed -1,840 MW bias is smaller than NESO's
2,582 MW mean embedded-wind estimate for the month (ratio ≈ 0.71), so roughly
700–900 MW looks like ordinary day-ahead forecast error sitting on top of the coverage
gap, not coverage alone. We also could not locate a single primary-source sentence
that pins down WINDFOR's exact scope definition — the conclusion rests on the
quantitative cross-check, not a documentation citation, and is stated with that
caveat.

**This does not affect `safe_volume_mw`.** Safe volume is an empirical quantile of the
*actual* error distribution, not a calculation that assumes errors average to zero —
it's correctly calibrated regardless of why the mean is negative. Full walkthrough in
`DEMO_SCRIPT.md`; the finding and numbers above also live in
`backend/app/services/accuracy_service.py` and are returned via the `/api/accuracy`
endpoint's `data_coverage_note` field.

## Deployment

**Frontend (Vercel)**: import the repo, set the project root to `frontend/`, build
command `npm run build`, output directory `dist`. Add env var
`VITE_API_BASE_URL=<your Render backend URL>`.

**Backend (Render)**: new Web Service, root directory `backend/`, environment
"Docker" (uses `backend/Dockerfile`). Add env var `CORS_ORIGINS` including your Vercel
domain (e.g. `https://your-app.vercel.app`), comma-separated if there's more than one
origin.

## AI tooling disclosure

This project was built with the assistance of Claude Code (Anthropic) for code
generation, debugging, and research (including the data-coverage investigation
above). All design decisions, verification, and final review were done by the author.
