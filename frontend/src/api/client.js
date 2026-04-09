// In dev mode (outside Telegram), use a mock initData
const DEV_INIT_DATA = 'user=%7B%22id%22%3A544665327%2C%22first_name%22%3A%22Ahmad%22%2C%22last_name%22%3A%22%22%2C%22username%22%3A%22admin%22%7D&auth_date=1700000000&hash=devhash'

function getInitData() {
  if (window.Telegram?.WebApp?.initData) {
    return window.Telegram.WebApp.initData
  }
  return DEV_INIT_DATA
}

async function request(method, path, body = null) {
  const opts = {
    method,
    headers: {
      'Content-Type': 'application/json',
      'X-Telegram-Init-Data': getInitData(),
    },
  }
  if (body !== null) {
    opts.body = JSON.stringify(body)
  }
  const res = await fetch(`/api${path}`, opts)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  // Schedule
  getTodaySchedule: () => request('GET', '/schedule/today'),

  // Supplements
  getSupplements: () => request('GET', '/supplements'),
  createSupplement: (data) => request('POST', '/supplements', data),
  deleteSupplement: (id) => request('DELETE', `/supplements/${id}`),

  // Intake
  intakeAction: (logId, action, snoozeMinutes = null) =>
    request('POST', `/intake/${logId}/action`, {
      action,
      snooze_minutes: snoozeMinutes,
    }),

  // Stock
  getStock: () => request('GET', '/stock'),
  updateStock: (supplementId, currentCount) =>
    request('PATCH', `/stock/${supplementId}`, { current_count: currentCount }),

  // Stats
  getStats: (period) => request('GET', `/stats?period=${period}`),

  // Me
  getMe: () => request('GET', '/me'),
}
