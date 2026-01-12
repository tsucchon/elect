import { useState, useEffect } from 'react'
import './App.css'
import { Dashboard } from './components/Dashboard'
import { healthCheck } from './services/api'

function App() {
  const [healthStatus, setHealthStatus] = useState<string>('checking...')

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const health = await healthCheck()
        setHealthStatus(health.status)
      } catch (error) {
        setHealthStatus('error')
        console.error('Health check failed:', error)
      }
    }

    checkHealth()
  }, [])

  return (
    <div className="App">
      <header className="App-header">
        <h1>再エネ発電量＋電力価格予測ダッシュボード</h1>
        <div className="header-status">
          <span className={`status-badge ${healthStatus}`}>
            API: {healthStatus}
          </span>
        </div>
      </header>
      <main>
        <Dashboard />
      </main>
      <footer className="App-footer">
        <p>Powered by LightGBM + Open-Meteo API</p>
      </footer>
    </div>
  )
}

export default App
