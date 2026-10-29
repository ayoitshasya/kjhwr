import type { ReactNode } from 'react'
import { useEffect, useState } from 'react'

export type Screen = 'decision' | 'accuracy'

interface LayoutProps {
  screen: Screen
  onScreenChange: (screen: Screen) => void
  children: ReactNode
}

function useTheme() {
  const [isDark, setIsDark] = useState(() => {
    try {
      const stored = localStorage.getItem('theme')
      if (stored) return stored === 'dark'
    } catch {
      // localStorage unavailable (private mode etc) - fall through to default
    }
    return true
  })

  useEffect(() => {
    document.body.classList.toggle('dark', isDark)
    try {
      localStorage.setItem('theme', isDark ? 'dark' : 'light')
    } catch {
      // best-effort only
    }
  }, [isDark])

  return { isDark, toggle: () => setIsDark((v) => !v) }
}

export function Layout({ screen, onScreenChange, children }: LayoutProps) {
  const { isDark, toggle } = useTheme()

  return (
    <div className="min-h-screen bg-(--color-bg) text-(--color-text)">
      <header className="border-b border-(--color-border)">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
          <div className="flex items-center gap-2">
            <span className="font-mono-tabular text-sm font-semibold tracking-tight">
              WIND DESK
            </span>
            <span className="hidden text-xs text-(--color-text-muted) sm:inline">
              GB wind · day-ahead · Jan 2026
            </span>
          </div>
          <nav className="flex items-center gap-1">
            <TabButton active={screen === 'decision'} onClick={() => onScreenChange('decision')}>
              Decision
            </TabButton>
            <TabButton active={screen === 'accuracy'} onClick={() => onScreenChange('accuracy')}>
              Accuracy
            </TabButton>
            <button
              type="button"
              onClick={toggle}
              aria-label="Toggle color theme"
              className="ml-2 rounded border border-(--color-border) px-2 py-1 text-xs text-(--color-text-muted) hover:text-(--color-text)"
            >
              {isDark ? 'dark' : 'light'}
            </button>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6">{children}</main>
    </div>
  )
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: ReactNode
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded px-3 py-1.5 text-sm font-medium transition-colors ${
        active
          ? 'bg-(--color-accent-forecast)/15 text-(--color-accent-forecast)'
          : 'text-(--color-text-muted) hover:text-(--color-text)'
      }`}
    >
      {children}
    </button>
  )
}
