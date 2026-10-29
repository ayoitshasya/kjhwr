// Mirrors backend/app/schemas/responses.py exactly - keep these two in sync by hand.

export interface HealthResponse {
  status: string
}

export interface ErrorResponse {
  error: {
    code: string
    message: string
  }
}

export interface ForecastPeriod {
  settlementPeriod: number
  startTime: string
  forecast_mw: number
  lower_band_mw: number
  upper_band_mw: number
}

export interface ForecastResponse {
  date: string
  confidence: number
  decision_publish_time: string
  cutoff_utc: string
  periods: ForecastPeriod[]
  total_forecast_mwh: number
  total_safe_volume_mwh: number
  implied_buffer_mwh: number
}

export interface ActualPeriod {
  settlementDate: string
  settlementPeriod: number
  startTime: string
  actual_mw: number
}

export interface ActualsResponse {
  date_from: string
  date_to: string
  periods: ActualPeriod[]
}

export interface ComparisonPeriod {
  settlementDate: string
  settlementPeriod: number
  startTime: string
  actual_mw: number
  forecast_mw: number
  error_mw: number
  decision_publish_time: string
  horizon_hours: number
}

export interface ComparisonResponse {
  date_from: string
  date_to: string
  periods: ComparisonPeriod[]
}

export interface QuantileSet {
  p10: number | null
  p50: number | null
  p90: number | null
}

export interface MetricsBlock {
  count: number
  mae_mw: number | null
  rmse_mw: number | null
  bias_mw: number | null
  mae_pct_of_mean: number | null
  mean_actual_mw: number | null
  quantiles_mw: QuantileSet
}

export interface SlicedMetricsBlock extends MetricsBlock {
  slice: string | number
}

export interface AccuracyResponse {
  date_from: string
  date_to: string
  confidence: number
  safe_volume_quantile_mw: number
  data_coverage_note: string
  overall: MetricsBlock
  by_settlement_period: SlicedMetricsBlock[]
  by_day: SlicedMetricsBlock[]
  by_horizon_bucket: SlicedMetricsBlock[]
  by_actual_decile: SlicedMetricsBlock[]
}
