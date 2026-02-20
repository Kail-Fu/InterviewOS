import { useEffect, useMemo, useState } from 'react'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export default function App() {
  const path = typeof window !== 'undefined' ? window.location.pathname : '/'

  if (path === '/dashboard') {
    return <DashboardPage />
  }

  if (path === '/take-assessment') {
    return <TakeAssessmentPlaceholder />
  }

  return <StartAssessmentPage />
}

function StartAssessmentPage() {
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
        <p className="subtitle">Open the admin dashboard at <code>/dashboard</code>.</p>

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

function DashboardPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [assessments, setAssessments] = useState([])
  const [selectedAssessmentId, setSelectedAssessmentId] = useState(null)
  const [candidates, setCandidates] = useState([])

  const assessmentsEndpoint = `${API_BASE_URL.replace(/\/$/, '')}/api/assessments`
  const candidatesEndpointBase = `${API_BASE_URL.replace(/\/$/, '')}/api/candidates`

  useEffect(() => {
    async function load() {
      setLoading(true)
      setError('')
      try {
        const response = await fetch(assessmentsEndpoint)
        if (!response.ok) {
          throw new Error('Failed to load assessments')
        }
        const payload = await response.json()
        const rows = payload.assessments || []
        setAssessments(rows)
        if (rows.length > 0) {
          setSelectedAssessmentId(rows[0].id)
        }
      } catch (loadError) {
        setError(loadError.message || 'Failed to load dashboard data')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [assessmentsEndpoint])

  useEffect(() => {
    if (!selectedAssessmentId) {
      setCandidates([])
      return
    }
    async function loadCandidates() {
      try {
        const endpoint = `${candidatesEndpointBase}?assessmentId=${selectedAssessmentId}`
        const response = await fetch(endpoint)
        if (!response.ok) {
          throw new Error('Failed to load candidates')
        }
        const payload = await response.json()
        setCandidates(payload.candidates || [])
      } catch {
        setCandidates([])
      }
    }
    loadCandidates()
  }, [candidatesEndpointBase, selectedAssessmentId])

  return (
    <main className="page page-wide">
      <section className="card card-wide">
        <p className="eyebrow">InterviewOS Admin</p>
        <h1>Dashboard</h1>
        <p className="subtitle">Assessment list foundation migrated from foretoken-demo dashboard flow.</p>

        {loading && <p>Loading assessments...</p>}
        {error && <p className="error">{error}</p>}

        {!loading && !error && (
          <div className="dashboard-grid">
            <div>
              <h2 className="section-title">Assessments</h2>
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Title</th>
                      <th>Role</th>
                      <th>Status</th>
                      <th>Candidates</th>
                    </tr>
                  </thead>
                  <tbody>
                    {assessments.map((assessment) => (
                      <tr
                        key={assessment.id}
                        className={selectedAssessmentId === assessment.id ? 'selected' : ''}
                        onClick={() => setSelectedAssessmentId(assessment.id)}
                      >
                        <td>{assessment.title}</td>
                        <td>{assessment.role}</td>
                        <td>{assessment.status}</td>
                        <td>{assessment.candidateCount}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div>
              <h2 className="section-title">Candidates</h2>
              <div className="table-wrap">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Email</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {candidates.map((candidate) => (
                      <tr key={candidate.id}>
                        <td>{candidate.name || '-'}</td>
                        <td>{candidate.email}</td>
                        <td>{candidate.status}</td>
                      </tr>
                    ))}
                    {candidates.length === 0 && (
                      <tr>
                        <td colSpan={3}>No candidates for this assessment yet.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        <div className="meta">
          <p><strong>Assessments API:</strong> {assessmentsEndpoint}</p>
          <p><strong>Candidates API:</strong> {candidatesEndpointBase}?assessmentId=&lt;id&gt;</p>
          <p><strong>Next:</strong> PR-05 ports create-assessment flow from NewAssessment + QuestionSelection.</p>
        </div>
      </section>
    </main>
  )
}

function TakeAssessmentPlaceholder() {
  const token = typeof window !== 'undefined'
    ? new URLSearchParams(window.location.search).get('token')
    : null

  return (
    <main className="page">
      <section className="card">
        <p className="eyebrow">InterviewOS Candidate</p>
        <h1>Take Assessment</h1>
        <p className="subtitle">
          Candidate execution UI is scheduled for PR-07. This route is now reserved and no longer mirrors the admin start page.
        </p>
        <div className="meta">
          <p><strong>Token detected:</strong> {token || '(none)'}</p>
          <p><strong>Expected now:</strong> invite verification APIs are ready; full candidate flow arrives in PR-07/PR-08.</p>
        </div>
      </section>
    </main>
  )
}
