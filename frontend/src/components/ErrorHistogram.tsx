import { useMemo } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { ComparisonPeriod } from '../api/types'

const BIN_COUNT = 20

function buildHistogram(errors: number[]) {
  if (errors.length === 0) return []
  const min = Math.min(...errors)
  const max = Math.max(...errors)
  const width = (max - min) / BIN_COUNT || 1

  const bins = Array.from({ length: BIN_COUNT }, (_, i) => ({
    binStart: min + i * width,
    count: 0,
  }))

  for (const e of errors) {
    const idx = Math.min(BIN_COUNT - 1, Math.floor((e - min) / width))
    bins[idx].count += 1
  }

  return bins.map((b) => ({
    label: Math.round(b.binStart).toLocaleString('en-GB'),
    count: b.count,
  }))
}

export function ErrorHistogram({ periods }: { periods: ComparisonPeriod[] }) {
  const data = useMemo(() => buildHistogram(periods.map((p) => p.error_mw)), [periods])

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 10, fill: 'var(--color-text-muted)' }}
            axisLine={{ stroke: 'var(--color-border)' }}
            tickLine={false}
            interval={1}
          />
          <YAxis
            tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }}
            axisLine={false}
            tickLine={false}
            width={32}
            allowDecimals={false}
          />
          <Tooltip
            contentStyle={{
              background: 'var(--color-panel)',
              border: '1px solid var(--color-border)',
              fontSize: 12,
              fontFamily: 'var(--font-mono)',
            }}
            labelFormatter={(label) => `error ≈ ${label} MW`}
          />
          <Bar dataKey="count" fill="var(--color-accent-forecast)" isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
