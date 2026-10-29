import type { SlicedMetricsBlock } from '../api/types'

const fmt = (v: number | null, digits = 0) => (v === null ? '—' : v.toFixed(digits))

export function MetricsTable({
  rows,
  sliceHeader,
  formatSlice = (s) => String(s),
}: {
  rows: SlicedMetricsBlock[]
  sliceHeader: string
  formatSlice?: (slice: string | number) => string
}) {
  return (
    <div className="overflow-x-auto rounded border border-(--color-border)">
      <table className="w-full min-w-[640px] text-sm">
        <thead>
          <tr className="border-b border-(--color-border) text-left text-xs uppercase tracking-wide text-(--color-text-muted)">
            <th className="px-3 py-2">{sliceHeader}</th>
            <th className="px-3 py-2 text-right">n</th>
            <th className="px-3 py-2 text-right">MAE (MW)</th>
            <th className="px-3 py-2 text-right">RMSE (MW)</th>
            <th className="px-3 py-2 text-right">Bias (MW)</th>
            <th className="px-3 py-2 text-right">MAE %</th>
            <th className="px-3 py-2 text-right">P10</th>
            <th className="px-3 py-2 text-right">P50</th>
            <th className="px-3 py-2 text-right">P90</th>
          </tr>
        </thead>
        <tbody className="font-mono-tabular">
          {rows.map((row) => (
            <tr key={String(row.slice)} className="border-b border-(--color-border)/60">
              <td className="px-3 py-1.5 font-sans text-(--color-text-muted)">
                {formatSlice(row.slice)}
              </td>
              <td className="px-3 py-1.5 text-right">{row.count}</td>
              <td className="px-3 py-1.5 text-right">{fmt(row.mae_mw)}</td>
              <td className="px-3 py-1.5 text-right">{fmt(row.rmse_mw)}</td>
              <td className="px-3 py-1.5 text-right">{fmt(row.bias_mw)}</td>
              <td className="px-3 py-1.5 text-right">{fmt(row.mae_pct_of_mean, 1)}</td>
              <td className="px-3 py-1.5 text-right">{fmt(row.quantiles_mw.p10)}</td>
              <td className="px-3 py-1.5 text-right">{fmt(row.quantiles_mw.p50)}</td>
              <td className="px-3 py-1.5 text-right">{fmt(row.quantiles_mw.p90)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
