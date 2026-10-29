import type { ReactNode } from 'react'
import { useState } from 'react'
import { useAccuracy, useComparison } from '../api/hooks'
import { ComparisonChart } from '../components/ComparisonChart'
import { ErrorHistogram } from '../components/ErrorHistogram'
import { ErrorOverTimeChart } from '../components/ErrorOverTimeChart'
import { HowToReadPanel } from '../components/HowToReadPanel'
import { MetricsTable } from '../components/MetricsTable'
import { QueryState } from '../components/QueryState'

const MIN_DATE = '2026-01-01'
const MAX_DATE = '2026-01-31'

type SliceDimension = 'settlement_period' | 'day' | 'horizon' | 'decile'

const SLICE_OPTIONS: { value: SliceDimension; label: string }[] = [
  { value: 'settlement_period', label: 'Time of day' },
  { value: 'day', label: 'Day' },
  { value: 'horizon', label: 'Forecast horizon' },
  { value: 'decile', label: 'Actual-generation decile' },
]

export function AccuracyView() {
  const [from, setFrom] = useState(MIN_DATE)
  const [to, setTo] = useState(MAX_DATE)
  const [sliceDimension, setSliceDimension] = useState<SliceDimension>('settlement_period')

  const comparisonQuery = useComparison(from, to)
  const accuracyQuery = useAccuracy(from, to, 0.9)

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end gap-4">
        <DateField label="From" value={from} onChange={setFrom} />
        <DateField label="To" value={to} onChange={setTo} />
      </div>

      <QueryState query={comparisonQuery} isEmpty={(d) => d.periods.length === 0}>
        {(data) => (
          <>
            <Panel title="Forecast vs actual">
              <ComparisonChart periods={data.periods} />
            </Panel>
            <Panel title="Error over time (actual − forecast)">
              <ErrorOverTimeChart periods={data.periods} />
            </Panel>
            <Panel title="Error distribution">
              <ErrorHistogram periods={data.periods} />
            </Panel>
          </>
        )}
      </QueryState>

      <QueryState query={accuracyQuery}>
        {(data) => (
          <Panel title="Metrics by slice">
            <div className="mb-3 flex flex-wrap gap-1">
              {SLICE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setSliceDimension(opt.value)}
                  className={`rounded px-2.5 py-1 text-xs font-medium ${
                    sliceDimension === opt.value
                      ? 'bg-(--color-accent-forecast)/15 text-(--color-accent-forecast)'
                      : 'text-(--color-text-muted) hover:text-(--color-text)'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
            {sliceDimension === 'settlement_period' && (
              <MetricsTable
                rows={data.by_settlement_period}
                sliceHeader="Settlement period"
                formatSlice={(s) => `SP ${s}`}
              />
            )}
            {sliceDimension === 'day' && (
              <MetricsTable rows={data.by_day} sliceHeader="Date" />
            )}
            {sliceDimension === 'horizon' && (
              <MetricsTable
                rows={data.by_horizon_bucket}
                sliceHeader="Horizon"
                formatSlice={(s) => `${s}–${Number(s) + 6}h`}
              />
            )}
            {sliceDimension === 'decile' && (
              <MetricsTable
                rows={data.by_actual_decile}
                sliceHeader="Actual decile"
                formatSlice={(s) => `D${s}`}
              />
            )}
          </Panel>
        )}
      </QueryState>

      <HowToReadPanel>
        <p>
          <strong>MAE</strong> (mean absolute error) and <strong>RMSE</strong> (root mean
          squared error) summarise typical forecast error size in MW - RMSE weights large
          misses more heavily. <strong>Bias</strong> is the average error (actual minus
          forecast): negative means the desk's forecast tends to run high. P10/P50/P90
          are the 10th/50th/90th percentile of the error distribution - the same
          quantiles used to build the Decision view's confidence band and safe volume.
        </p>
        <p>
          Slicing by time of day and forecast horizon shows whether error is worse at
          particular settlement periods or further-ahead forecasts; slicing by
          actual-generation decile shows whether the forecast is systematically worse in
          very low or very high wind conditions.
        </p>
      </HowToReadPanel>
    </div>
  )
}

function DateField({
  label,
  value,
  onChange,
}: {
  label: string
  value: string
  onChange: (v: string) => void
}) {
  return (
    <label className="flex flex-col gap-1 text-xs text-(--color-text-muted)">
      {label}
      <input
        type="date"
        value={value}
        min={MIN_DATE}
        max={MAX_DATE}
        onChange={(e) => onChange(e.target.value)}
        className="rounded border border-(--color-border) bg-(--color-panel) px-2 py-1.5 font-mono-tabular text-sm text-(--color-text)"
      />
    </label>
  )
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded border border-(--color-border) bg-(--color-panel) p-4">
      <div className="mb-3 text-xs uppercase tracking-wide text-(--color-text-muted)">
        {title}
      </div>
      {children}
    </div>
  )
}
