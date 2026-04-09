import { useState, useEffect } from 'react'
import BottomNav from './components/BottomNav'
import TodayPage from './pages/TodayPage'
import SupplementsPage from './pages/SupplementsPage'
import StockPage from './pages/StockPage'
import StatsPage from './pages/StatsPage'
import './styles/global.css'

export default function App() {
  const [tab, setTab] = useState('today')

  useEffect(() => {
    const tg = window.Telegram?.WebApp
    if (tg) {
      tg.ready()
      tg.expand()
    }
  }, [])

  const pages = {
    today: <TodayPage />,
    supplements: <SupplementsPage />,
    stock: <StockPage />,
    stats: <StatsPage />,
  }

  return (
    <>
      {pages[tab]}
      <BottomNav active={tab} onChange={setTab} />
    </>
  )
}
