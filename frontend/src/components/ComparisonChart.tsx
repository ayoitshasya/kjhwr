import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { ComparisonPeriod } from '../api/types'

function formatDate(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', timeZone: 'UTC' })
}

export function ComparisonChart({ periods }: { periods: ComparisonPeriod[] }) {
  const rows = periods.map((p) => ({
    date: formatDate(p.startTime),
    actual_mw: p.actual_mw,
    forecast_mw: p.forecast_mw,
  }))

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={rows} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
          <XAxis
            dataKey="date"
            interval={Math.ceil(rows.length / 10)}
            tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }}
            axisLine={{ stroke: 'var(--color-border)' }}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }}
            axisLine={false}
            tickLine={false}
            width={56}
            tickFormatter={(v: number) => `${Math.round(v / 1000)}GW`}
          />
          <Tooltip
            contentStyle={{
              background: 'var(--color-panel)',
              border: '1px solid var(--color-border)',
              fontSize: 12,
              fontFamily: 'var(--font-mono)',
            }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line
            dataKey="actual_mw"
            name="Actual"
            stroke="var(--color-accent-actual)"
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
          <Line
            dataKey="forecast_mw"
            name="Decision-time forecast"
            stroke="var(--color-accent-forecast)"
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
