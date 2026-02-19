import { useMemo, useState } from 'react'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export default function App() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState('')
  const [error, setError] = useState('')

  const endpoint = useMemo(() => `${API_BASE_URL.replace(/\/$/, '')}/assessments/start`, [])

  async function onSubmit(event) {
    event.preventDefault()
    setLoading(true)
    setSuccess('')
    setError('')

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      })

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}))
        throw new Error(payload.detail || 'Request failed')
      }

      setSuccess('Assessment sent. Check backend logs or your inbox provider.')
      setEmail('')
    } catch (submitError) {
      setError(submitError.message || 'Failed to send assessment')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="page">
      <section className="card">
        <p className="eyebrow">InterviewOS Demo</p>
        <h1>Start Assessment</h1>
        <p className="subtitle">Open-source local flow: send a candidate invite email from your own backend.</p>

        <form onSubmit={onSubmit} className="form">
          <label htmlFor="email">Candidate Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="candidate@example.com"
            required
          />

          <button type="submit" disabled={loading}>
            {loading ? 'Sending...' : 'Start Assessment'}
          </button>
        </form>

        {success && <p className="success">{success}</p>}
        {error && <p className="error">{error}</p>}

        <div className="meta">
          <p><strong>API:</strong> {endpoint}</p>
          <p><strong>Tips:</strong> In local default mode, emails print to backend logs.</p>
        </div>
      </section>
    </main>
  )
}
