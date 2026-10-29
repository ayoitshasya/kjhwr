import { useQuery } from '@tanstack/react-query'
import { api } from './client'

export function useForecast(date: string, confidence: number) {
  return useQuery({
    queryKey: ['forecast', date, confidence],
    queryFn: () => api.forecast(date, confidence),
  })
}

export function useComparison(from: string, to: string) {
  return useQuery({
    queryKey: ['comparison', from, to],
    queryFn: () => api.comparison(from, to),
  })
}

export function useAccuracy(from: string, to: string, confidence: number) {
  return useQuery({
    queryKey: ['accuracy', from, to, confidence],
    queryFn: () => api.accuracy(from, to, confidence),
  })
}
