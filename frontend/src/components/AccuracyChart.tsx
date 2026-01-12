import type { AccuracyResponse } from '../types'
import './AccuracyChart.css'

interface AccuracyChartProps {
  data: AccuracyResponse | null
}

export const AccuracyChart = ({ data }: AccuracyChartProps) => {
  if (!data) {
    return (
      <div className="accuracy-chart-container">
        <p className="no-data">精度データがありません</p>
      </div>
    )
  }

  const getAccuracyLevel = (mape: number | null): string => {
    if (mape === null) return 'データなし'
    if (mape < 5) return '優秀'
    if (mape < 10) return '良好'
    if (mape < 20) return '普通'
    return '要改善'
  }

  const getAccuracyColor = (mape: number | null): string => {
    if (mape === null) return '#999'
    if (mape < 5) return '#4caf50'
    if (mape < 10) return '#8bc34a'
    if (mape < 20) return '#ff9800'
    return '#f44336'
  }

  return (
    <div className="accuracy-chart-container">
      <p className="period-info">過去 {data.period_days} 日間の予測精度</p>

      <div className="accuracy-cards">
        <div className="accuracy-card">
          <h4>発電量予測</h4>
          <div
            className="mape-value"
            style={{ color: getAccuracyColor(data.generation_mape) }}
          >
            {data.generation_mape !== null
              ? `${data.generation_mape.toFixed(2)}%`
              : 'データなし'}
          </div>
          <div className="accuracy-level">
            {getAccuracyLevel(data.generation_mape)}
          </div>
        </div>

        <div className="accuracy-card">
          <h4>価格予測</h4>
          <div
            className="mape-value"
            style={{ color: getAccuracyColor(data.price_mape) }}
          >
            {data.price_mape !== null
              ? `${data.price_mape.toFixed(2)}%`
              : 'データなし'}
          </div>
          <div className="accuracy-level">
            {getAccuracyLevel(data.price_mape)}
          </div>
        </div>
      </div>

      <div className="mape-explanation">
        <p><strong>MAPE (平均絶対パーセント誤差)</strong></p>
        <p>予測値と実測値の誤差率を示す指標です。値が小さいほど精度が高いことを示します。</p>
        <ul>
          <li>&lt; 5%: 優秀な予測精度</li>
          <li>&lt; 10%: 良好な予測精度</li>
          <li>&lt; 20%: 普通の予測精度</li>
          <li>≥ 20%: 改善が必要</li>
        </ul>
      </div>

      {(data.generation_mape === null && data.price_mape === null) && (
        <div className="no-data-message">
          実績データと予測データの両方が必要です。CSVをアップロードして予測を実行してください。
        </div>
      )}
    </div>
  )
}
