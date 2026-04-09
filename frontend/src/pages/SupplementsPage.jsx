import { useState, useEffect } from 'react'
import { api } from '../api/client'
import AddSupplementModal from '../components/AddSupplementModal'
import './SupplementsPage.css'

export default function SupplementsPage() {
  const [supplements, setSupplements] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [deleting, setDeleting] = useState(null)

  const load = async () => {
    try {
      const data = await api.getSupplements()
      setSupplements(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Удалить «${name}»?\nВсе напоминания будут отключены.`)) return
    setDeleting(id)
    try {
      await api.deleteSupplement(id)
      await load()
    } catch (e) {
      alert(e.message)
    } finally {
      setDeleting(null)
    }
  }

  const handleAdded = () => {
    setShowModal(false)
    load()
  }

  if (loading) return <div className="spinner" />

  return (
    <div className="page">
      <h1 className="page-title">Мои БАД</h1>

      {supplements.length === 0 && (
        <div className="empty">
          <div className="empty-icon">💊</div>
          <div className="empty-text">Нет добавленных БАД.<br />Нажмите + чтобы добавить</div>
        </div>
      )}

      {supplements.map(sup => (
        <div key={sup.id} className="sup-card">
          <div className="sup-card__header">
            <div className="sup-card__name">{sup.name}</div>
            <button
              className="sup-card__delete"
              onClick={() => handleDelete(sup.id, sup.name)}
              disabled={deleting === sup.id}
            >
              🗑
            </button>
          </div>
          <div className="sup-card__meta">
            <span>💊 {sup.dose_per_intake} шт. за приём</span>
            {sup.stock && (
              <span className={sup.stock.current_count <= sup.stock.reorder_threshold ? 'text-warn' : ''}>
                📦 {sup.stock.current_count} шт.
                {sup.stock.current_count <= sup.stock.reorder_threshold && ' ⚠️'}
              </span>
            )}
          </div>
          {sup.schedules.length > 0 && (
            <div className="sup-card__times">
              {sup.schedules.map(s => (
                <span key={s.id} className="time-chip">
                  ⏰ {String(s.hour).padStart(2,'0')}:{String(s.minute).padStart(2,'0')}
                </span>
              ))}
            </div>
          )}
        </div>
      ))}

      <button className="fab" onClick={() => setShowModal(true)}>+</button>

      {showModal && (
        <AddSupplementModal
          onClose={() => setShowModal(false)}
          onAdded={handleAdded}
        />
      )}
    </div>
  )
}
