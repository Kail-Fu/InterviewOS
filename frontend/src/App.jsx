import { useEffect, useMemo, useState } from 'react'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function navigateTo(path) {
  window.location.href = path
}

function apiUrl(path) {
  return `${API_BASE_URL.replace(/\/$/, '')}${path}`
}

export default function App() {
  const path = typeof window !== 'undefined' ? window.location.pathname : '/'

  if (path === '/dashboard') {
    return <DashboardPage />
  }

  if (path === '/new-assessment') {
    return <NewAssessmentPage />
  }

  if (path === '/selection-questions') {
    return <QuestionSelectionPage />
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

  const endpoint = useMemo(() => apiUrl('/assessments/start'), [])

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

  const assessmentsEndpoint = apiUrl('/api/assessments')
  const candidatesEndpointBase = apiUrl('/api/candidates')

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

        <div className="actions-row">
          <button type="button" onClick={() => navigateTo('/new-assessment')}>New Assessment</button>
        </div>

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
          <p><strong>Create flow:</strong> <code>/new-assessment</code> -> <code>/selection-questions</code></p>
        </div>
      </section>
    </main>
  )
}

function NewAssessmentPage() {
  const [title, setTitle] = useState('')
  const [jobLink, setJobLink] = useState('')
  const [jobDesc, setJobDesc] = useState('')
  const [error, setError] = useState('')
  const [checking, setChecking] = useState(false)
  const [loadingTitle, setLoadingTitle] = useState(true)

  useEffect(() => {
    async function loadDefaultTitle() {
      try {
        const response = await fetch(apiUrl('/api/assessments'))
        const payload = await response.json().catch(() => ({ assessments: [] }))
        const existing = (payload.assessments || []).map((item) => item.title)

        const now = new Date()
        const dateLabel = `${now.getMonth() + 1}/${now.getDate()}`
        const baseTitle = `${dateLabel} Software Engineer`
        let unique = baseTitle
        let counter = 2
        while (existing.includes(unique)) {
          unique = `${baseTitle} (${counter})`
          counter += 1
        }
        setTitle(unique)
      } catch {
        setTitle('New Assessment')
      } finally {
        setLoadingTitle(false)
      }
    }
    loadDefaultTitle()
  }, [])

  async function onNext(event) {
    event.preventDefault()
    const cleanTitle = title.trim()
    if (!cleanTitle) {
      setError('Title is required.')
      return
    }

    setChecking(true)
    setError('')
    try {
      const response = await fetch(`${apiUrl('/api/assessments/check-title')}?title=${encodeURIComponent(cleanTitle)}`)
      if (!response.ok) {
        throw new Error('Unable to verify title right now.')
      }
      const payload = await response.json()
      if (payload.exists) {
        setError('An assessment with this name already exists.')
        return
      }
      const params = new URLSearchParams({
        title: cleanTitle,
        jobLink,
        jobDesc,
      })
      navigateTo(`/selection-questions?${params.toString()}`)
    } catch (nextError) {
      setError(nextError.message || 'Unable to verify title right now.')
    } finally {
      setChecking(false)
    }
  }

  return (
    <main className="page">
      <section className="card">
        <p className="eyebrow">InterviewOS Admin</p>
        <h1>New Assessment</h1>
        <p className="subtitle">Step 1 of 2: define title and context, then pick a question pack.</p>

        <form onSubmit={onNext} className="form">
          <label htmlFor="title">Title*</label>
          <input
            id="title"
            value={title}
            disabled={loadingTitle}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Assessment title"
            required
          />

          <label htmlFor="jobLink">Job Opening Link</label>
          <input
            id="jobLink"
            value={jobLink}
            onChange={(event) => setJobLink(event.target.value)}
            placeholder="https://..."
          />

          <label htmlFor="jobDesc">Job Description</label>
          <textarea
            id="jobDesc"
            rows={4}
            value={jobDesc}
            onChange={(event) => setJobDesc(event.target.value)}
            placeholder="Optional role context"
          />

          <button type="submit" disabled={checking || loadingTitle}>
            {checking ? 'Checking...' : 'Select Questions'}
          </button>
          <button type="button" className="secondary" onClick={() => navigateTo('/dashboard')}>
            Cancel
          </button>
        </form>

        {error && <p className="error">{error}</p>}
      </section>
    </main>
  )
}

function QuestionSelectionPage() {
  const params = new URLSearchParams(window.location.search)
  const title = params.get('title') || 'Untitled Assessment'
  const jobLink = params.get('jobLink') || ''
  const jobDesc = params.get('jobDesc') || ''

  const [questions, setQuestions] = useState([])
  const [selected, setSelected] = useState(null)
  const [error, setError] = useState('')
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    async function loadQuestions() {
      try {
        const response = await fetch(apiUrl('/api/questions'))
        if (!response.ok) {
          throw new Error('Failed to load questions')
        }
        const payload = await response.json()
        setQuestions(payload || [])
      } catch (loadError) {
        setError(loadError.message || 'Failed to load questions')
      }
    }
    loadQuestions()
  }, [])

  async function createNewAssessment() {
    if (!selected) {
      setError('Please select a question first.')
      return
    }
    setCreating(true)
    setError('')
    try {
      const response = await fetch(apiUrl('/api/new-assessments'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          jobLink,
          jobDesc,
          questionId: selected.id,
        }),
      })
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}))
        throw new Error(payload.detail || 'Failed to create assessment')
      }
      navigateTo('/dashboard')
    } catch (createError) {
      setError(createError.message || 'Failed to create assessment')
    } finally {
      setCreating(false)
    }
  }

  return (
    <main className="page page-wide">
      <section className="card card-wide">
        <p className="eyebrow">InterviewOS Admin</p>
        <h1>Select Questions</h1>
        <p className="subtitle">Step 2 of 2: choose a template question set for <strong>{title}</strong>.</p>

        {error && <p className="error">{error}</p>}

        <div className="question-grid">
          {questions.map((question) => (
            <button
              key={question.id}
              type="button"
              className={`question-card ${selected?.id === question.id ? 'question-card-selected' : ''}`}
              onClick={() => setSelected(question)}
            >
              <p className="question-title">{question.title}</p>
              <p className="question-meta">{question.role} • {question.language} • {question.difficulty}</p>
              <p className="question-summary">{question.summary}</p>
              <p className="question-time">Estimated: {question.estimatedTime}</p>
            </button>
          ))}
        </div>

        <div className="actions-row">
          <button type="button" className="secondary" onClick={() => navigateTo('/new-assessment')}>
            Back
          </button>
          <button type="button" onClick={createNewAssessment} disabled={creating || !selected}>
            {creating ? 'Creating...' : 'Create Assessment'}
          </button>
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
