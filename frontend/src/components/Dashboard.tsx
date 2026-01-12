import { ForecastChart } from './ForecastChart'
import { AccuracyChart } from './AccuracyChart'
import { UploadPanel } from './UploadPanel'
import { usePrediction } from '../hooks/usePrediction'
import { useAccuracy } from '../hooks/useAccuracy'
import './Dashboard.css'

export const Dashboard = () => {
  const { data: predictions, loading: predictLoading, error: predictError, refetch: refetchPrediction } = usePrediction()
  const { data: accuracy, loading: accuracyLoading, refetch: refetchAccuracy } = useAccuracy()

  const handleUploadSuccess = () => {
    // アップロード成功後、予測と精度を再取得
    refetchPrediction()
    refetchAccuracy()
  }

  if (predictLoading) {
    return (
      <div className="dashboard">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>予測データを読み込み中...</p>
        </div>
      </div>
    )
  }

  if (predictError) {
    return (
      <div className="dashboard">
        <div className="error-container">
          <h2>エラーが発生しました</h2>
          <p>{predictError}</p>
          <button onClick={refetchPrediction} className="retry-button">再試行</button>
          <div className="error-hint">
            <p><strong>ヒント:</strong></p>
            <ul>
              <li>モデルが学習されていない可能性があります。<code>ml/scripts/train.py</code>を実行してください。</li>
              <li>バックエンドが起動していることを確認してください。</li>
            </ul>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>再エネ発電量＋電力価格 予測ダッシュボード</h2>
        <p className="subtitle">東京エリア - 次の48時間予測</p>
      </div>

      <UploadPanel onUploadSuccess={handleUploadSuccess} />

      <div className="dashboard-grid">
        <div className="dashboard-panel left-panel">
          <h3>📈 次の48時間予測</h3>
          {predictions && <ForecastChart data={predictions} />}
        </div>

        <div className="dashboard-panel right-panel">
          <h3>🎯 過去7日間の精度（MAPE）</h3>
          {accuracyLoading ? (
            <div className="loading-small">読み込み中...</div>
          ) : (
            <AccuracyChart data={accuracy} />
          )}
        </div>
      </div>

      {predictions && (
        <div className="info-footer">
          <p>
            予測生成時刻: {new Date(predictions.generated_at).toLocaleString('ja-JP')}
          </p>
        </div>
      )}
    </div>
  )
}
