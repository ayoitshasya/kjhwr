import type { UseQueryResult } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { ApiError } from '../api/client'

interface QueryStateProps<T> {
  query: UseQueryResult<T>
  isEmpty?: (data: T) => boolean
  emptyMessage?: string
  children: (data: T) => ReactNode
}

/** Loading / empty / error handling shared across every chart and table on both screens. */
export function QueryState<T>({
  query,
  isEmpty,
  emptyMessage = 'No data available for this selection.',
  children,
}: QueryStateProps<T>) {
  if (query.isPending) {
    return (
      <div className="flex items-center justify-center py-16 text-sm text-(--color-text-muted)">
        <span className="animate-pulse font-mono-tabular">loading…</span>
      </div>
    )
  }

  if (query.isError) {
    const message = query.error instanceof ApiError ? query.error.message : 'Request failed.'
    return (
      <div className="rounded border border-(--color-accent-negative)/40 bg-(--color-accent-negative)/10 px-4 py-3 text-sm text-(--color-accent-negative)">
        <span className="font-semibold">Couldn't load this view.</span> {message}
      </div>
    )
  }

  const data = query.data as T
  if (isEmpty?.(data)) {
    return (
      <div className="flex items-center justify-center py-16 text-sm text-(--color-text-muted)">
        {emptyMessage}
      </div>
    )
  }

  return <>{children(data)}</>
}
