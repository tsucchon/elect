/**
 * APIクライアント
 */

import type { DataStatus, PredictionResponse, AccuracyResponse } from '../types'

const API_BASE = '/api'

/**
 * データ状態を取得
 */
export const getDataStatus = async (): Promise<DataStatus> => {
  const response = await fetch(`${API_BASE}/data/status`)
  if (!response.ok) {
    throw new Error('Failed to fetch data status')
  }
  return response.json()
}

/**
 * ヘルスチェック
 */
export const healthCheck = async () => {
  const response = await fetch(`${API_BASE}/health`)
  if (!response.ok) {
    throw new Error('Health check failed')
  }
  return response.json()
}

/**
 * 最新予測を取得
 */
export const getLatestPrediction = async (area: string = 'tokyo', hours: number = 48): Promise<PredictionResponse> => {
  const response = await fetch(`${API_BASE}/predict/latest?area=${area}&hours=${hours}`)
  if (!response.ok) {
    throw new Error('Failed to fetch prediction')
  }
  return response.json()
}

/**
 * 精度データを取得
 */
export const getAccuracy = async (area: string = 'tokyo', days: number = 7): Promise<AccuracyResponse> => {
  const response = await fetch(`${API_BASE}/predict/accuracy?area=${area}&days=${days}`)
  if (!response.ok) {
    throw new Error('Failed to fetch accuracy')
  }
  return response.json()
}
