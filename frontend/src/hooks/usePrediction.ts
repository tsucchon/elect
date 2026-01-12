import { useState, useEffect, useCallback } from 'react'
import { getLatestPrediction } from '../services/api'
import type { PredictionResponse } from '../types'

export const usePrediction = (area: string = 'tokyo', hours: number = 48) => {
  const [data, setData] = useState<PredictionResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const result = await getLatestPrediction(area, hours)
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : '予測データの取得に失敗しました')
      console.error('Failed to fetch prediction:', err)
    } finally {
      setLoading(false)
    }
  }, [area, hours])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return {
    data,
    loading,
    error,
    refetch: fetchData
  }
}
