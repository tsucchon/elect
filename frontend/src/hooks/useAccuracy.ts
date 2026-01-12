import { useState, useEffect, useCallback } from 'react'
import { getAccuracy } from '../services/api'
import type { AccuracyResponse } from '../types'

export const useAccuracy = (area: string = 'tokyo', days: number = 7) => {
  const [data, setData] = useState<AccuracyResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const result = await getAccuracy(area, days)
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : '精度データの取得に失敗しました')
      console.error('Failed to fetch accuracy:', err)
    } finally {
      setLoading(false)
    }
  }, [area, days])

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
