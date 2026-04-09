import './BottomNav.css'

const TABS = [
  { id: 'today', label: 'Сегодня', icon: '📋' },
  { id: 'supplements', label: 'БАД', icon: '💊' },
  { id: 'stock', label: 'Остатки', icon: '📦' },
  { id: 'stats', label: 'Статистика', icon: '📊' },
]

export default function BottomNav({ active, onChange }) {
  return (
    <nav className="bottom-nav">
      {TABS.map(tab => (
        <button
          key={tab.id}
          className={`nav-item ${active === tab.id ? 'nav-item--active' : ''}`}
          onClick={() => onChange(tab.id)}
        >
          <span className="nav-icon">{tab.icon}</span>
          <span className="nav-label">{tab.label}</span>
        </button>
      ))}
    </nav>
  )
}
