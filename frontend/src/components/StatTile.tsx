export function StatTile({
  label,
  value,
  unit,
  accent,
}: {
  label: string
  value: string
  unit?: string
  accent?: 'forecast' | 'actual' | 'negative' | 'neutral'
}) {
  const accentClass =
    accent === 'forecast'
      ? 'text-(--color-accent-forecast)'
      : accent === 'actual'
        ? 'text-(--color-accent-actual)'
        : accent === 'negative'
          ? 'text-(--color-accent-negative)'
          : 'text-(--color-text)'

  return (
    <div className="rounded border border-(--color-border) bg-(--color-panel) px-4 py-3">
      <div className="text-xs uppercase tracking-wide text-(--color-text-muted)">{label}</div>
      <div className={`mt-1 font-mono-tabular text-2xl font-semibold ${accentClass}`}>
        {value}
        {unit && <span className="ml-1 text-sm font-normal text-(--color-text-muted)">{unit}</span>}
      </div>
    </div>
  )
}
