import { useState } from 'react'
import { api } from '../api/client'
import './AddSupplementModal.css'

export default function AddSupplementModal({ onClose, onAdded }) {
  const [name, setName] = useState('')
  const [dose, setDose] = useState(1)
  const [times, setTimes] = useState([])
  const [timeInput, setTimeInput] = useState('')
  const [stockCount, setStockCount] = useState('')
  const [threshold, setThreshold] = useState('10')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const addTime = () => {
    const t = timeInput.trim()
    if (!/^\d{1,2}:\d{2}$/.test(t)) { setError('Формат: ЧЧ:ММ'); return }
    const [h, m] = t.split(':').map(Number)
    if (h > 23 || m > 59) { setError('Недопустимое время'); return }
    const formatted = `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}`
    if (!times.includes(formatted)) setTimes([...times, formatted])
    setTimeInput('')
    setError('')
  }

  const removeTime = (t) => setTimes(times.filter(x => x !== t))

  const handleSubmit = async () => {
    if (!name.trim()) { setError('Введите название'); return }
    if (times.length === 0) { setError('Добавьте хотя бы одно время'); return }
    if (stockCount === '') { setError('Введите количество в запасе'); return }

    setLoading(true)
    setError('')
    try {
      await api.createSupplement({
        name: name.trim(),
        dose_per_intake: dose,
        times,
        stock_count: parseInt(stockCount) || 0,
        reorder_threshold: parseInt(threshold) || 10,
      })
      onAdded()
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal-sheet">
        <div className="modal-handle" />
        <div className="modal-title">Добавить БАД</div>

        {error && <div className="modal-error">{error}</div>}

        <div className="input-group">
          <label className="input-label">Название</label>
          <input
            className="input"
            placeholder="Omega-3 Mentor"
            value={name}
            onChange={e => setName(e.target.value)}
          />
        </div>

        <div className="input-group">
          <label className="input-label">Доза (шт. за приём)</label>
          <div className="dose-stepper">
            <button className="stepper-btn" onClick={() => setDose(d => Math.max(1, d - 1))}>−</button>
            <span className="stepper-val">{dose}</span>
            <button className="stepper-btn" onClick={() => setDose(d => Math.min(20, d + 1))}>+</button>
          </div>
        </div>

        <div className="input-group">
          <label className="input-label">Время приёма</label>
          <div className="time-input-row">
            <input
              className="input"
              placeholder="08:00"
              value={timeInput}
              onChange={e => setTimeInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && addTime()}
            />
            <button className="btn btn-primary btn-sm" onClick={addTime}>+</button>
          </div>
          {times.length > 0 && (
            <div className="time-chips">
              {times.map(t => (
                <span key={t} className="time-chip-removable" onClick={() => removeTime(t)}>
                  ⏰ {t} ✕
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="input-group">
          <label className="input-label">Запас (шт.)</label>
          <input
            className="input"
            type="number"
            placeholder="60"
            value={stockCount}
            onChange={e => setStockCount(e.target.value)}
          />
        </div>

        <div className="input-group">
          <label className="input-label">Алерт при остатке ниже</label>
          <input
            className="input"
            type="number"
            placeholder="10"
            value={threshold}
            onChange={e => setThreshold(e.target.value)}
          />
        </div>

        <button
          className="btn btn-primary"
          style={{ width: '100%', marginTop: 8 }}
          onClick={handleSubmit}
          disabled={loading}
        >
          {loading ? 'Сохраняем...' : 'Добавить БАД'}
        </button>
        <button
          className="btn btn-ghost"
          style={{ width: '100%', marginTop: 8 }}
          onClick={onClose}
        >
          Отмена
        </button>
      </div>
    </div>
  )
}
