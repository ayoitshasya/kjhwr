import { useState } from 'react'
import { useForecast } from '../api/hooks'
import { ForecastChart } from '../components/ForecastChart'
import { HowToReadPanel } from '../components/HowToReadPanel'
import { QueryState } from '../components/QueryState'
import { StatTile } from '../components/StatTile'

const MIN_DATE = '2026-01-01'
const MAX_DATE = '2026-01-31'
const DEFAULT_DATE = '2026-01-15'
const CONFIDENCE_OPTIONS = [0.8, 0.9, 0.95]

const fmtMwh = (v: number) => Math.round(v).toLocaleString('en-GB')

export function DecisionView() {
  const [date, setDate] = useState(DEFAULT_DATE)
  const [confidence, setConfidence] = useState(0.9)
  const query = useForecast(date, confidence)

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end gap-4">
        <label className="flex flex-col gap-1 text-xs text-(--color-text-muted)">
          Delivery day
          <input
            type="date"
            value={date}
            min={MIN_DATE}
            max={MAX_DATE}
            onChange={(e) => setDate(e.target.value)}
            className="rounded border border-(--color-border) bg-(--color-panel) px-2 py-1.5 font-mono-tabular text-sm text-(--color-text)"
          />
        </label>
        <label className="flex flex-col gap-1 text-xs text-(--color-text-muted)">
          Confidence level
          <select
            value={confidence}
            onChange={(e) => setConfidence(Number(e.target.value))}
            className="rounded border border-(--color-border) bg-(--color-panel) px-2 py-1.5 font-mono-tabular text-sm text-(--color-text)"
          >
            {CONFIDENCE_OPTIONS.map((c) => (
              <option key={c} value={c}>
                {Math.round(c * 100)}%
              </option>
            ))}
          </select>
        </label>
      </div>

      <QueryState query={query}>
        {(data) => (
          <>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <StatTile
                label="Forecast volume"
                value={fmtMwh(data.total_forecast_mwh)}
                unit="MWh"
                accent="forecast"
              />
              <StatTile
                label={`Safe volume @ ${Math.round(data.confidence * 100)}%`}
                value={fmtMwh(data.total_safe_volume_mwh)}
                unit="MWh"
                accent="actual"
              />
              <StatTile
                label="Risk buffer"
                value={fmtMwh(data.implied_buffer_mwh)}
                unit="MWh"
                accent="negative"
              />
            </div>

            <div className="rounded border border-(--color-border) bg-(--color-panel) p-4">
              <div className="mb-3 flex items-center justify-between text-xs text-(--color-text-muted)">
                <span>Half-hourly forecast, decided {formatDecisionTime(data.decision_publish_time)}</span>
                <span>Gate closure {formatDecisionTime(data.cutoff_utc)}</span>
              </div>
              <ForecastChart periods={data.periods} />
            </div>

            <HowToReadPanel>
              <p>
                The line is the <strong>decision-time forecast</strong>: the latest wind
                forecast published before 11:00 UK time on the day before delivery, which
                is the only forecast the desk could actually have acted on at gate
                closure. The shaded band is the empirical P10–P90 range of forecast error
                observed across January 2026 - 80% of the time, actual generation has
                landed within that band around the forecast.
              </p>
              <p>
                <strong>Safe volume</strong> is the forecast minus a margin sized from
                historical error: at {Math.round(data.confidence * 100)}% confidence, it's
                the forecast plus the {Math.round((1 - data.confidence) * 100)}th
                percentile of past errors (a negative number), giving a volume that
                actual generation has met or exceeded {Math.round(data.confidence * 100)}%
                of the time historically. The{' '}
                <strong>risk buffer</strong> (forecast − safe volume) is how much extra
                thermal generation the desk should be ready to buy to cover the downside.
              </p>
              <p>
                Note: FUELHH actuals (used to derive the error margin above) only cover
                Balancing-Mechanism-metered wind farms, not all of GB wind - confirmed
                against NESO&apos;s own embedded-wind data. See the Accuracy view&apos;s
                &quot;how to read this&quot; panel and the README for what that means and
                why the safe-volume figure is still reliable despite it.
              </p>
            </HowToReadPanel>
          </>
        )}
      </QueryState>
    </div>
  )
}

function formatDecisionTime(iso: string): string {
  const d = new Date(iso)
  return `${d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', timeZone: 'UTC' })} ${d.toLocaleTimeString(
    'en-GB',
    { hour: '2-digit', minute: '2-digit', timeZone: 'UTC' },
  )} UTC`
}
