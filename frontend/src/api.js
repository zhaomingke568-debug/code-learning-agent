export const API_BASE = 'http://localhost:8000'

export const api = {
  async startSession(topic, depthLevel, threadId = null) {
    const res = await fetch(`${API_BASE}/api/sessions/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic, depthLevel, threadId })
    })
    return res.json()
  },

  async getState(threadId) {
    const res = await fetch(`${API_BASE}/api/sessions/${threadId}/state`)
    return res.json()
  },

  async recoverSession(threadId) {
    const res = await fetch(`${API_BASE}/api/sessions/${threadId}/recover`, { method: 'POST' })
    return res.json()
  },

  async getExplanation(threadId) {
    const res = await fetch(`${API_BASE}/api/content/explanation/${threadId}`)
    return res.json()
  },

  async getExercise(threadId) {
    const res = await fetch(`${API_BASE}/api/content/exercise/${threadId}`)
    return res.json()
  },

  async getLearningPath(threadId) {
    const res = await fetch(`${API_BASE}/api/content/learning-path/${threadId}`)
    return res.json()
  },

  async submitCode(threadId, code) {
    const res = await fetch(`${API_BASE}/api/execution/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ threadId, code })
    })
    return res.json()
  },

  async submitFeedback(threadId, feedback) {
    const res = await fetch(`${API_BASE}/api/feedback/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ threadId, feedback })
    })
    return res.json()
  },

  async getReport(threadId) {
    const res = await fetch(`${API_BASE}/api/report/${threadId}`)
    return res.json()
  },

  async submitAssessment(threadId, answers) {
    const res = await fetch(`${API_BASE}/api/assessment/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ threadId, answers })
    })
    return res.json()
  }
}

export function useSSE(threadId) {
  const [events, setEvents] = React.useState([])

  React.useEffect(() => {
    if (!threadId) return

    const eventSource = new EventSource(`${API_BASE}/api/stream/${threadId}`)

    eventSource.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        setEvents(prev => [...prev, { type: e.type || 'message', data }])
      } catch (err) {
        console.error('SSE parse error:', err)
      }
    }

    eventSource.onerror = (e) => {
      console.error('SSE error:', e)
    }

    return () => eventSource.close()
  }, [threadId])

  return events
}