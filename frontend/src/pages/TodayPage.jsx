import { useState, useEffect } from 'react'
import { Check, X, Clock, Pill } from 'lucide-react'
import { api } from '../api/client'
import './TodayPage.css'

const STATUS_LABEL = {
  taken: 'Принято',
  skipped: 'Пропущено',
  pending: 'Ожидает',
  snoozed: 'Отложено',
}

const STATUS_CLASS = {
  taken: 'badge-taken',
  skipped: 'badge-skipped',
  pending: 'badge-pending',
  snoozed: 'badge-snoozed',
}

export default function TodayPage() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [acting, setActing] = useState(null)

  const load = async () => {
    try {
      const data = await api.getTodaySchedule()
      setLogs(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleAction = async (logId, action, snoozeMin = null) => {
    setActing(logId)
    try {
      await api.intakeAction(logId, action, snoozeMin)
      await load()
    } catch (e) {
      alert(e.message)
    } finally {
      setActing(null)
    }
  }

  if (loading) return <div className="spinner" />

  const pending = logs.filter(l => l.status === 'pending' || l.status === 'snoozed')
  const done = logs.filter(l => l.status === 'taken' || l.status === 'skipped')

  return (
    <div className="page">
      <h1 className="page-title">Сегодня</h1>

      {logs.length === 0 && (
        <div className="empty">
          <div className="empty-icon"><Pill size={48} strokeWidth={1.5} /></div>
          <div className="empty-text">Нет запланированных приёмов.<br />Добавьте БАД во вкладке «БАД»</div>
        </div>
      )}

      {pending.length > 0 && (
        <div className="section">
          <div className="section-label">Ожидают приёма</div>
          {pending.map(log => (
            <div key={log.log_id} className="today-card">
              <div className="today-card__header">
                <div className="today-card__time">{log.scheduled_time}</div>
                <div className="today-card__name">{log.supplement_name}</div>
                <span className={`badge ${STATUS_CLASS[log.status]}`}>{STATUS_LABEL[log.status]}</span>
              </div>
              <div className="today-card__dose">Доза: {log.dose} шт.</div>
              <div className="today-card__actions">
                <button
                  className="btn btn-primary btn-sm"
                  disabled={acting === log.log_id}
                  onClick={() => handleAction(log.log_id, 'taken')}
                >
                  <Check size={14} /> Принял
                </button>
                <button
                  className="btn btn-secondary btn-sm"
                  disabled={acting === log.log_id}
                  onClick={() => handleAction(log.log_id, 'skip')}
                >
                  <X size={14} /> Пропустить
                </button>
                <button
                  className="btn btn-ghost btn-sm"
                  disabled={acting === log.log_id}
                  onClick={() => handleAction(log.log_id, 'snooze', 30)}
                >
                  <Clock size={14} /> +30 мин
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {done.length > 0 && (
        <div className="section">
          <div className="section-label">Выполнено</div>
          {done.map(log => (
            <div key={log.log_id} className={`today-card today-card--done`}>
              <div className="today-card__header">
                <div className="today-card__time">{log.scheduled_time}</div>
                <div className="today-card__name">{log.supplement_name}</div>
                <span className={`badge ${STATUS_CLASS[log.status]}`}>{STATUS_LABEL[log.status]}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
