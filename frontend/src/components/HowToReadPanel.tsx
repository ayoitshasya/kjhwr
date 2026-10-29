import type { ReactNode } from 'react'

export function HowToReadPanel({ children }: { children: ReactNode }) {
  return (
    <details className="rounded border border-(--color-border) bg-(--color-panel) px-4 py-3 text-sm open:pb-4">
      <summary className="cursor-pointer select-none font-medium text-(--color-text-muted)">
        How to read this
      </summary>
      <div className="mt-3 space-y-2 text-(--color-text-muted)">{children}</div>
    </details>
  )
}
