import { useState, useEffect } from 'react'
import { api } from '../api/client'
import './StatsPage.css'

export default function StatsPage() {
  const [period, setPeriod] = useState(7)
  const [stats, setStats] = useState([])
  const [loading, setLoading] = useState(true)

  const load = async (p) => {
    setLoading(true)
    try {
      const data = await api.getStats(p)
      setStats(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load(period) }, [period])

  return (
    <div className="page">
      <h1 className="page-title">Статистика</h1>

      <div className="period-tabs">
        <button
          className={`period-tab ${period === 7 ? 'period-tab--active' : ''}`}
          onClick={() => setPeriod(7)}
        >
          7 дней
        </button>
        <button
          className={`period-tab ${period === 30 ? 'period-tab--active' : ''}`}
          onClick={() => setPeriod(30)}
        >
          30 дней
        </button>
      </div>

      {loading && <div className="spinner" />}

      {!loading && stats.length === 0 && (
        <div className="empty">
          <div className="empty-icon">📊</div>
          <div className="empty-text">Нет данных за выбранный период</div>
        </div>
      )}

      {!loading && stats.map(s => (
        <div key={s.supplement_id} className="stats-card">
          <div className="stats-card__name">{s.supplement_name}</div>
          <div className="progress-bar" style={{ margin: '10px 0 6px' }}>
            <div className="progress-fill" style={{ width: `${s.percent}%` }} />
          </div>
          <div className="stats-card__row">
            <span className="stats-pct">{s.percent}% принято</span>
            <div className="stats-counts">
              <span className="stats-taken">✅ {s.taken}</span>
              <span className="stats-skipped">❌ {s.skipped}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
