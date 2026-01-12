import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import type { PredictionResponse } from '../types'
import './ForecastChart.css'

interface ForecastChartProps {
  data: PredictionResponse
}

export const ForecastChart = ({ data }: ForecastChartProps) => {
  // データ整形
  const chartData = data.predictions.generation.map((gen, i) => {
    const timestamp = new Date(gen.timestamp)
    const formattedTime = timestamp.toLocaleString('ja-JP', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })

    return {
      time: formattedTime,
      timestamp: gen.timestamp,
      発電量: Math.round(gen.value * 10) / 10,
      価格: Math.round(data.predictions.price[i].value * 10) / 10
    }
  })

  return (
    <div className="forecast-chart-container">
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="time"
            angle={-45}
            textAnchor="end"
            height={80}
            interval={Math.floor(chartData.length / 12)}
          />
          <YAxis
            yAxisId="left"
            label={{ value: '発電量 (MW)', angle: -90, position: 'insideLeft' }}
            stroke="#8884d8"
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            label={{ value: '価格 (円/kWh)', angle: 90, position: 'insideRight' }}
            stroke="#82ca9d"
          />
          <Tooltip
            contentStyle={{ backgroundColor: '#fff', border: '1px solid #ccc' }}
            labelStyle={{ fontWeight: 'bold' }}
          />
          <Legend wrapperStyle={{ paddingTop: '20px' }} />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="発電量"
            stroke="#8884d8"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 6 }}
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="価格"
            stroke="#82ca9d"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
