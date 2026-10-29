import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { ForecastPeriod } from '../api/types'

function formatTime(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', timeZone: 'UTC' })
}

const fmtMw = (v: number) => `${Math.round(v).toLocaleString('en-GB')} MW`

export function ForecastChart({ periods }: { periods: ForecastPeriod[] }) {
  const rows = periods.map((p) => ({
    time: formatTime(p.startTime),
    forecast_mw: p.forecast_mw,
    band: [p.lower_band_mw, p.upper_band_mw] as [number, number],
  }))

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={rows} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
          <XAxis
            dataKey="time"
            interval={5}
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
            formatter={(value, name) => {
              if (name === 'band' && Array.isArray(value)) {
                return [`${fmtMw(value[0])} – ${fmtMw(value[1])}`, 'P10–P90 range']
              }
              return [fmtMw(value as number), 'Forecast']
            }}
          />
          <Area
            dataKey="band"
            stroke="none"
            fill="var(--color-band)"
            isAnimationActive={false}
          />
          <Line
            dataKey="forecast_mw"
            stroke="var(--color-accent-forecast)"
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
