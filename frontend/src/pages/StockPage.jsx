import { useState, useEffect } from 'react'
import { api } from '../api/client'
import './StockPage.css'

export default function StockPage() {
  const [stocks, setStocks] = useState([])
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(null)
  const [editVal, setEditVal] = useState('')
  const [saving, setSaving] = useState(null)

  const load = async () => {
    try {
      const data = await api.getStock()
      setStocks(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const startEdit = (s) => {
    setEditing(s.supplement_id)
    setEditVal(String(s.current_count))
  }

  const saveEdit = async (supplementId) => {
    const val = parseInt(editVal)
    if (isNaN(val) || val < 0) { setEditing(null); return }
    setSaving(supplementId)
    try {
      await api.updateStock(supplementId, val)
      await load()
    } catch (e) {
      alert(e.message)
    } finally {
      setSaving(null)
      setEditing(null)
    }
  }

  if (loading) return <div className="spinner" />

  return (
    <div className="page">
      <h1 className="page-title">Остатки</h1>

      {stocks.length === 0 && (
        <div className="empty">
          <div className="empty-icon">📦</div>
          <div className="empty-text">Нет данных. Добавьте БАД во вкладке «БАД»</div>
        </div>
      )}

      {stocks.map(s => {
        const pct = Math.min(100, Math.round((s.current_count / Math.max(s.reorder_threshold * 3, 1)) * 100))
        const isLow = s.is_low

        return (
          <div key={s.supplement_id} className={`stock-card ${isLow ? 'stock-card--low' : ''}`}>
            <div className="stock-card__header">
              <div className="stock-card__name">{s.supplement_name}</div>
              {isLow && <span className="low-badge">⚠️ Мало</span>}
            </div>

            <div className="stock-card__count-row">
              <span className="stock-label">Остаток:</span>
              {editing === s.supplement_id ? (
                <div className="edit-row">
                  <input
                    className="input count-input"
                    type="number"
                    value={editVal}
                    onChange={e => setEditVal(e.target.value)}
                    autoFocus
                  />
                  <button
                    className="btn btn-primary btn-sm"
                    disabled={saving === s.supplement_id}
                    onClick={() => saveEdit(s.supplement_id)}
                  >
                    {saving === s.supplement_id ? '...' : '✓'}
                  </button>
                  <button className="btn btn-secondary btn-sm" onClick={() => setEditing(null)}>✕</button>
                </div>
              ) : (
                <span className="stock-count" onClick={() => startEdit(s)}>
                  {s.current_count} шт. ✏️
                </span>
              )}
            </div>

            <div className="progress-bar" style={{ margin: '10px 0 6px' }}>
              <div
                className="progress-fill"
                style={{
                  width: `${pct}%`,
                  background: isLow ? 'var(--warning)' : 'var(--primary)',
                }}
              />
            </div>
            <div className="stock-threshold">Порог заказа: {s.reorder_threshold} шт.</div>
          </div>
        )
      })}
    </div>
  )
}
