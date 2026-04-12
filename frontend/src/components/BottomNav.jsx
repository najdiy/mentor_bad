import { CalendarCheck, Pill, Package, BarChart3 } from 'lucide-react'
import './BottomNav.css'

const TABS = [
  { id: 'today', label: 'Сегодня', Icon: CalendarCheck },
  { id: 'supplements', label: 'БАД', Icon: Pill },
  { id: 'stock', label: 'Остатки', Icon: Package },
  { id: 'stats', label: 'Статистика', Icon: BarChart3 },
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
          <tab.Icon size={22} strokeWidth={active === tab.id ? 2.2 : 1.8} />
          <span className="nav-label">{tab.label}</span>
        </button>
      ))}
    </nav>
  )
}
