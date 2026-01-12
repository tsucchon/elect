/**
 * 型定義
 */

// 予測データポイント
export interface PredictionPoint {
  timestamp: string
  value: number
}

// 予測レスポンス
export interface PredictionResponse {
  area: string
  predictions: {
    generation: PredictionPoint[]
    price: PredictionPoint[]
  }
  generated_at: string
}

// 精度データ
export interface AccuracyResponse {
  area: string
  period_days: number
  generation_mape: number | null
  price_mape: number | null
  note: string
}

// データ状態
export interface DataStatus {
  generation: {
    count: number
    latest_timestamp: string | null
  }
  price: {
    count: number
    latest_timestamp: string | null
  }
}
