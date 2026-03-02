import { useEffect, useMemo, useState } from 'react'
import Assessment from './Assessment'
import ReportPage from './pages/Report'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function navigateTo(path) {
  window.location.href = path
}

function apiUrl(path) {
  return `${API_BASE_URL.replace(/\/$/, '')}${path}`
}

export default function App() {
  const path = typeof window !== 'undefined' ? window.location.pathname : '/'
  const assessmentResultMatch = path.match(/^\/assessment_result\/(\d+)$/)
  const reportMatch = path.match(/^\/report\/(.+)$/)
  const loadingMatch = path.match(/^\/[^/]+\/loading\/(.+)$/)

  if (path === '/dashboard') {
    return <AdminShell><DashboardPage /></AdminShell>
  }

  if (assessmentResultMatch) {
    return <AdminShell><AssessmentResultPage assessmentId={Number(assessmentResultMatch[1])} /></AdminShell>
  }

  if (reportMatch) {
    return <AdminShell><ReportPage reportId={reportMatch[1]} /></AdminShell>
  }

  if (loadingMatch) {
    return <LoadingPlaceholder assessmentId={loadingMatch[1]} />
  }

  if (path === '/new-assessment') {
    return <AdminShell><NewAssessmentPage /></AdminShell>
  }

  if (path === '/selection-questions') {
    return <AdminShell><QuestionSelectionPage /></AdminShell>
  }

  if (path === '/take-assessment') {
    return <TakeAssessmentGateway />
  }

  return <AdminShell><StartAssessmentPage /></AdminShell>
}

function AdminShell({ children }) {
  return <div className="io-admin">{children}</div>
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
                      <th>Actions</th>
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
                        <td>
                          <button
                            type="button"
                            className="inline-btn"
                            onClick={(event) => {
                              event.stopPropagation()
                              navigateTo(`/assessment_result/${assessment.id}`)
                            }}
                          >
                            Open
                          </button>
                        </td>
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
          <p><strong>Create flow:</strong> <code>/new-assessment</code> {'->'} <code>/selection-questions</code></p>
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
  const [previewQuestion, setPreviewQuestion] = useState(null)
  const [error, setError] = useState('')
  const [creating, setCreating] = useState(false)

  const QUESTION_DETAILS = {
    'Users API': {
      overview:
        'Work in a production-style backend and deliver robust API behavior under realistic engineering constraints.',
      detailedDescription:
        'You will work in an existing backend codebase and implement practical API changes under realistic constraints. This measures implementation quality, debugging, and API design judgment.',
      tasks: [
        { title: 'Fix API edge cases', description: 'Handle malformed/invalid identifiers and return correct status codes.' },
        { title: 'Extend filtering behavior', description: 'Support robust query filtering behavior and predictable response shape.' },
        { title: 'Implement inactive-user logic', description: 'Add endpoint logic and validate behavior with deterministic tests.' },
      ],
      skillsTested: ['Node.js', 'Express', 'REST API', 'Debugging', 'Testing'],
      evaluationCriteria: [
        'Endpoint correctness and status code behavior',
        'Readability and maintainability of implementation',
        'Edge-case handling and defensive logic',
        'Testing completeness and reliability',
      ],
      deliverables: ['Updated backend implementation', 'Passing test evidence', 'Clear submission package'],
      allowedResources: 'Public documentation, package references, and your local development tooling.',
    },
    'Supreme Court Q&A RAG System': {
      overview:
        'Design and implement a retrieval-augmented generation system that returns grounded legal Q&A answers.',
      detailedDescription:
        'Build a retrieval-augmented QA workflow over legal-style material, with focus on retrieval quality, answer grounding, and system design decisions.',
      tasks: [
        { title: 'Ingest and index source material', description: 'Set up retrieval pipeline and document chunking/index strategy.' },
        { title: 'Implement answer generation flow', description: 'Return grounded answers with strong retrieval-to-generation linkage.' },
        { title: 'Handle failure/edge behavior', description: 'Provide deterministic behavior for weak retrieval or ambiguous queries.' },
      ],
      skillsTested: ['RAG Systems', 'LLM App Design', 'Retrieval', 'Prompting', 'Evaluation'],
      evaluationCriteria: [
        'Grounding quality and retrieval relevance',
        'System robustness and error handling',
        'Code clarity and architecture choices',
        'Reasoning quality in final reflection',
      ],
      deliverables: ['Working RAG implementation', 'Runnable instructions', 'Submission archive + reflection'],
      allowedResources: 'Public documentation, package references, and your local development tooling.',
    },
    'Named Entity Recognition (NER) - Product Attributes': {
      overview:
        'Train and evaluate a practical NER workflow focused on extracting product attributes from real-world text.',
      detailedDescription:
        'Train/evaluate an NER workflow focused on product attributes and explain model behavior across in-domain and out-of-domain data.',
      tasks: [
        { title: 'Implement training/evaluation', description: 'Train model and compute meaningful evaluation metrics.' },
        { title: 'Analyze ID vs OOD behavior', description: 'Compare quality across in-domain and out-of-domain inputs.' },
        { title: 'Document tradeoffs and next steps', description: 'Explain model limitations and practical improvements.' },
      ],
      skillsTested: ['NER', 'ML Evaluation', 'Error Analysis', 'Python', 'Modeling'],
      evaluationCriteria: [
        'Metric quality and interpretation',
        'Clarity of modeling decisions',
        'Practicality of improvements proposed',
        'Submission completeness and reproducibility',
      ],
      deliverables: ['Training/evaluation artifact', 'Evaluation outputs', 'Submission archive + reflection'],
      allowedResources: 'Public documentation, package references, and your local development tooling.',
    },
    'Insurance Document Processor - LlamaIndex API': {
      overview:
        'Build a document-to-JSON extraction pipeline for insurance records with stable schema-aligned outputs.',
      detailedDescription:
        'Process insurance-style documents into structured JSON and produce stable extraction behavior with schema-aligned outputs.',
      tasks: [
        { title: 'Implement extraction pipeline', description: 'Build parsing/extraction flow for target fields.' },
        { title: 'Constrain outputs to schema', description: 'Ensure deterministic and valid JSON outputs.' },
        { title: 'Improve reliability', description: 'Handle malformed or ambiguous inputs robustly.' },
      ],
      skillsTested: ['LlamaIndex', 'Information Extraction', 'JSON Schema', 'Backend Engineering'],
      evaluationCriteria: [
        'Extraction correctness and consistency',
        'Schema adherence and output quality',
        'Robustness to input variation',
        'Code quality and maintainability',
      ],
      deliverables: ['Working processor implementation', 'Structured JSON outputs', 'Submission archive + reflection'],
      allowedResources: 'Public documentation, package references, and your local development tooling.',
    },
  }

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

  async function createNewAssessment(questionOverride = null) {
    const chosenQuestion = questionOverride || selected
    if (!chosenQuestion) {
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
          questionId: chosenQuestion.id,
        }),
      })
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}))
        throw new Error(payload.detail || 'Failed to create assessment')
      }
      const payload = await response.json()
      navigateTo(`/assessment_result/${payload.id}?openInvite=1`)
    } catch (createError) {
      setError(createError.message || 'Failed to create assessment')
    } finally {
      setCreating(false)
    }
  }

  function getDifficultyColor(difficulty) {
    const level = (difficulty || '').toLowerCase()
    if (level === 'easy') return 'bg-emerald-50 text-emerald-700 border-emerald-200'
    if (level === 'medium') return 'bg-amber-50 text-amber-700 border-amber-200'
    if (level === 'hard') return 'bg-rose-50 text-rose-700 border-rose-200'
    return 'bg-gray-50 text-gray-700 border-gray-200'
  }

  return (
    <main className="page page-wide">
      <section className="card card-wide">
        <p className="eyebrow">InterviewOS Admin</p>
        <h1>Select Questions</h1>
        <p className="subtitle">Step 2 of 2: choose a template question set for <strong>{title}</strong>.</p>

        {error && <p className="error">{error}</p>}

        <div style={{ display: 'grid', gap: 12 }}>
          {questions.map((question) => (
            <button
              key={question.id}
              type="button"
              className={`question-card ${selected?.id === question.id ? 'question-card-selected' : ''}`}
              onClick={() => {
                setSelected(question)
                setPreviewQuestion(question)
              }}
            >
              <p className="question-title">{question.title}</p>
              <p className="question-meta">{question.role} • {question.language} • {question.difficulty}</p>
              <p className="question-summary">{question.summary}</p>
              <p className="question-time">Estimated: {question.estimatedTime}</p>
              <p className="question-open">Click to preview full assessment details</p>
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

        {previewQuestion && (
          <div className="modal-backdrop" onClick={(event) => {
            if (event.target === event.currentTarget) {
              setPreviewQuestion(null)
            }
          }}>
            <div className="modal-panel modal-panel-rich">
              {(() => {
                const details = QUESTION_DETAILS[previewQuestion.title] || {}
                return (
                  <>
                    <div className="modal-header">
                      <div>
                        <h2 style={{ marginBottom: 8 }}>{previewQuestion.title}</h2>
                        <div className="actions-row" style={{ marginTop: 0, marginBottom: 0 }}>
                          <span className={`inline-btn ${getDifficultyColor(previewQuestion.difficulty)}`} style={{ border: '1px solid #d1d5db' }}>
                            {previewQuestion.difficulty}
                          </span>
                          <span className="inline-btn" style={{ border: '1px solid #d1d5db' }}>{previewQuestion.role}</span>
                          <span className="inline-btn" style={{ border: '1px solid #d1d5db' }}>{previewQuestion.language}</span>
                        </div>
                      </div>
                      <button
                        type="button"
                        className="secondary"
                        onClick={() => setPreviewQuestion(null)}
                        style={{ marginTop: 0 }}
                      >
                        Close
                      </button>
                    </div>

                    <div style={{ display: 'grid', gap: 14, paddingBottom: 8 }}>
                      <div>
                        <p className="question-title" style={{ marginBottom: 6 }}>Summary</p>
                        <p className="question-summary" style={{ marginBottom: 0 }}>{previewQuestion.summary}</p>
                      </div>

                      {(details.overview || previewQuestion.overview) && (
                        <div>
                          <p className="question-title" style={{ marginBottom: 6 }}>Overview</p>
                          <p className="question-summary" style={{ marginBottom: 0 }}>
                            {details.overview || previewQuestion.overview}
                          </p>
                        </div>
                      )}

                      {(details.detailedDescription || previewQuestion.detailedDescription) && (
                        <div className="detail-box">
                          <p className="question-title" style={{ marginBottom: 6 }}>Detailed Description</p>
                          <p className="question-summary" style={{ marginBottom: 0 }}>
                            {details.detailedDescription || previewQuestion.detailedDescription}
                          </p>
                        </div>
                      )}

                      <div className="detail-highlight">
                        <p style={{ margin: 0, fontWeight: 700 }}>Estimated Time</p>
                        <p style={{ margin: '4px 0 0' }}>{previewQuestion.estimatedTime}</p>
                      </div>

                      {Array.isArray(details.tasks) && details.tasks.length > 0 && (
                        <div>
                          <p className="question-title" style={{ marginBottom: 8 }}>Key Tasks</p>
                          <div style={{ display: 'grid', gap: 10 }}>
                            {details.tasks.map((task, idx) => (
                              <div key={`${task.title}-${idx}`} className="task-row">
                                <span className="task-index">{idx + 1}</span>
                                <div style={{ display: 'grid', gap: 2 }}>
                                  <p style={{ margin: 0, fontWeight: 700 }}>{task.title}</p>
                                  <p style={{ margin: 0, color: '#4b5563' }}>{task.description}</p>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {Array.isArray(details.skillsTested) && details.skillsTested.length > 0 && (
                        <div>
                          <p className="question-title" style={{ marginBottom: 8 }}>Skills Assessed</p>
                          <div className="actions-row" style={{ margin: 0, flexWrap: 'wrap' }}>
                            {details.skillsTested.map((skill) => (
                              <span key={skill} className="inline-btn" style={{ border: '1px solid #d1d5db' }}>
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {Array.isArray(details.evaluationCriteria) && details.evaluationCriteria.length > 0 && (
                        <div>
                          <p className="question-title" style={{ marginBottom: 8 }}>Evaluation Criteria</p>
                          <ul style={{ margin: 0, paddingLeft: 18 }}>
                            {details.evaluationCriteria.map((item, idx) => (
                              <li key={`${idx}-${item}`} style={{ marginBottom: 6 }}>{item}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {Array.isArray(details.deliverables) && details.deliverables.length > 0 && (
                        <div>
                          <p className="question-title" style={{ marginBottom: 8 }}>Deliverables</p>
                          <ul style={{ margin: 0, paddingLeft: 18 }}>
                            {details.deliverables.map((item, idx) => (
                              <li key={`${idx}-${item}`} style={{ marginBottom: 6 }}>{item}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {details.allowedResources && (
                        <div className="detail-success">
                          <p style={{ margin: 0, fontWeight: 700 }}>Allowed Resources</p>
                          <p style={{ margin: '4px 0 0' }}>{details.allowedResources}</p>
                        </div>
                      )}

                      <div className="result-header" style={{ marginBottom: 0 }}>
                        <p style={{ margin: 0 }}><strong>Evaluation Flow:</strong> {previewQuestion.assessmentType}</p>
                      </div>
                    </div>

                    <div className="modal-footer">
                      <button type="button" className="secondary" onClick={() => setPreviewQuestion(null)}>
                        Cancel
                      </button>
                      <button
                        type="button"
                        onClick={async () => {
                          setSelected(previewQuestion)
                          setPreviewQuestion(null)
                          await createNewAssessment(previewQuestion)
                        }}
                        disabled={creating}
                      >
                        {creating ? 'Creating...' : 'Confirm Selection'}
                      </button>
                    </div>
                  </>
                )
              })()}
            </div>
          </div>
        )}
      </section>
    </main>
  )
}

function AssessmentResultPage({ assessmentId }) {
  const newInviteRow = () => ({
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`,
    name: '',
    email: '',
  })

  const [assessment, setAssessment] = useState(null)
  const [candidates, setCandidates] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showInvite, setShowInvite] = useState(false)
  const [sending, setSending] = useState(false)
  const [inviteList, setInviteList] = useState([newInviteRow()])
  const [inviteFormError, setInviteFormError] = useState('')
  const [inviteFieldErrors, setInviteFieldErrors] = useState({})
  const [toast, setToast] = useState(null)

  useEffect(() => {
    if (!toast) {
      return
    }
    const timer = setTimeout(() => setToast(null), 2600)
    return () => clearTimeout(timer)
  }, [toast])

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    if (params.get('openInvite') === '1') {
      setShowInvite(true)
    }
  }, [])

  useEffect(() => {
    async function load() {
      setLoading(true)
      setError('')
      try {
        const [assessmentRes, candidatesRes] = await Promise.all([
          fetch(apiUrl(`/api/assessments/${assessmentId}`)),
          fetch(apiUrl(`/api/candidates?assessmentId=${assessmentId}`)),
        ])
        if (!assessmentRes.ok) {
          throw new Error('Failed to load assessment')
        }
        if (!candidatesRes.ok) {
          throw new Error('Failed to load candidates')
        }
        const assessmentPayload = await assessmentRes.json()
        const candidatesPayload = await candidatesRes.json()
        setAssessment(assessmentPayload)
        setCandidates(candidatesPayload.candidates || [])
      } catch (loadError) {
        setError(loadError.message || 'Failed to load assessment result')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [assessmentId])

  async function sendInvites() {
    setInviteFormError('')
    setInviteFieldErrors({})

    const isValidEmail = (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)
    const fieldErrors = {}
    const cleaned = []

    for (const row of inviteList) {
      const name = row.name.trim()
      const email = row.email.trim()
      const touched = name.length > 0 || email.length > 0
      if (!touched) {
        continue
      }
      if (!email) {
        fieldErrors[row.id] = 'Email is required for this row.'
        continue
      }
      if (!isValidEmail(email)) {
        fieldErrors[row.id] = 'Enter a valid email address'
        continue
      }
      cleaned.push({ rowId: row.id, name, email })
    }

    if (Object.keys(fieldErrors).length > 0) {
      setInviteFieldErrors(fieldErrors)
      return
    }

    if (cleaned.length === 0) {
      setInviteFormError('Add at least one candidate email before sending invites.')
      return
    }
    setSending(true)
    try {
      const response = await fetch(apiUrl('/api/invite/bulk'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          assessmentId,
          candidates: cleaned.map((item) => ({ name: item.name, email: item.email })),
        }),
      })
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}))
        if (Array.isArray(payload.detail)) {
          const apiFieldErrors = {}
          for (const detail of payload.detail) {
            const msg = 'Enter a valid email address'
            const loc = Array.isArray(detail?.loc) ? detail.loc : []
            const candidateIndex = loc.length >= 3 && typeof loc[2] === 'number' ? loc[2] : null
            if (candidateIndex != null && cleaned[candidateIndex]) {
              apiFieldErrors[cleaned[candidateIndex].rowId] = msg
            }
          }
          if (Object.keys(apiFieldErrors).length > 0) {
            setInviteFieldErrors(apiFieldErrors)
            setInviteFormError('')
            return
          }
          setInviteFormError('Invite validation failed.')
          return
        }
        const detail = typeof payload.detail === 'string' ? payload.detail : 'Failed to send invites'
        setInviteFormError(detail)
        return
      }
      const refreshed = await fetch(apiUrl(`/api/candidates?assessmentId=${assessmentId}`))
      if (refreshed.ok) {
        const payload = await refreshed.json()
        setCandidates(payload.candidates || [])
      }
      setInviteList([newInviteRow()])
      setShowInvite(false)
      setToast(`Invites sent to ${cleaned.length} candidate${cleaned.length > 1 ? 's' : ''}.`)
    } catch (sendError) {
      setInviteFormError(sendError.message || 'Failed to send invites')
    } finally {
      setSending(false)
    }
  }

  async function resendInvite(candidate) {
    try {
      const response = await fetch(apiUrl('/api/invite/resend'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          assessmentId,
          candidateId: candidate.id,
          email: candidate.email,
        }),
      })
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}))
        throw new Error(payload.detail || 'Failed to resend invite')
      }
      const refreshed = await fetch(apiUrl(`/api/candidates?assessmentId=${assessmentId}`))
      if (refreshed.ok) {
        const payload = await refreshed.json()
        setCandidates(payload.candidates || [])
      }
      setToast(`Invite resent to ${candidate.email}.`)
    } catch (resendError) {
      setError(resendError.message || 'Failed to resend invite')
    }
  }

  function addInviteRow() {
    setInviteList((rows) => [...rows, newInviteRow()])
  }

  function updateInvite(index, field, value) {
    setInviteList((rows) => rows.map((row, i) => (i === index ? { ...row, [field]: value } : row)))
    const rowId = inviteList[index]?.id
    if (rowId && inviteFieldErrors[rowId]) {
      setInviteFieldErrors((current) => {
        const next = { ...current }
        delete next[rowId]
        return next
      })
    }
    if (inviteFormError) {
      setInviteFormError('')
    }
  }

  function removeInvite(index) {
    setInviteList((rows) => rows.filter((_, i) => i !== index))
  }

  function renderStatus(candidate) {
    if (candidate.status === 'resent' && candidate.invitedAt) {
      return `resent at ${new Date(candidate.invitedAt).toLocaleString()}`
    }
    return candidate.status
  }

  return (
    <main className="page page-wide">
      <section className="card card-wide">
        <p className="eyebrow">InterviewOS Admin</p>
        <h1>Assessment Result</h1>
        <p className="subtitle">Parity slice for foretoken-demo AssessmentResult flow.</p>

        <div className="actions-row">
          <button type="button" className="secondary" onClick={() => navigateTo('/dashboard')}>
            Back
          </button>
          <button type="button" onClick={() => setShowInvite(true)}>
            Invite Candidates
          </button>
        </div>

        {loading && <p>Loading assessment...</p>}
        {error && <p className="error">{error}</p>}

        {!loading && assessment && (
          <>
            <div className="result-header">
              <p><strong>Title:</strong> {assessment.title}</p>
              <p><strong>Role:</strong> {assessment.role}</p>
              <p><strong>Status:</strong> {assessment.status}</p>
              {assessment.question && (
                <p><strong>Question:</strong> {assessment.question.title}</p>
              )}
            </div>

            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Status</th>
                    <th>Invited At</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {candidates.map((candidate) => (
                    <tr key={candidate.id}>
                      <td>{candidate.name || '-'}</td>
                      <td>{candidate.email}</td>
                      <td>{renderStatus(candidate)}</td>
                      <td>{new Date(candidate.invitedAt).toLocaleString()}</td>
                      <td>
                        <div className="actions-row" style={{ margin: 0 }}>
                          <button
                            type="button"
                            className="inline-btn"
                            onClick={() => resendInvite(candidate)}
                          >
                            Resend Invite
                          </button>
                          <button
                            type="button"
                            className="inline-btn"
                            onClick={() => navigateTo(`/report/${candidate.id}`)}
                          >
                            View Report
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {candidates.length === 0 && (
                    <tr>
                      <td colSpan={5}>No candidates yet.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}

        {showInvite && (
          <div className="modal-backdrop">
            <div className="modal-panel">
              <h2>Invite Candidates</h2>
              {inviteFormError && <p className="error inline-error">{inviteFormError}</p>}
              <div className="form">
                {inviteList.map((invite, index) => (
                  <div className="invite-row" key={invite.id}>
                    <div className="invite-field">
                      <input
                        type="text"
                        placeholder="Name"
                        value={invite.name}
                        onChange={(event) => updateInvite(index, 'name', event.target.value)}
                      />
                    </div>
                    <div className="invite-field">
                      <input
                        type="email"
                        placeholder="Email"
                        value={invite.email}
                        onChange={(event) => updateInvite(index, 'email', event.target.value)}
                        className={inviteFieldErrors[invite.id] ? 'input-error' : ''}
                      />
                      {inviteFieldErrors[invite.id] && (
                        <p className="field-error">{inviteFieldErrors[invite.id]}</p>
                      )}
                    </div>
                    {inviteList.length > 1 && (
                      <button type="button" className="secondary" onClick={() => removeInvite(index)}>
                        Remove
                      </button>
                    )}
                  </div>
                ))}
                <div className="actions-row">
                  <button type="button" className="secondary" onClick={addInviteRow}>
                    Add Row
                  </button>
                  <button type="button" className="secondary" onClick={() => setShowInvite(false)}>
                    Cancel
                  </button>
                  <button type="button" disabled={sending} onClick={sendInvites}>
                    {sending ? 'Sending...' : 'Send Invites'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
        {toast && (
          <div className="toast success-toast">{toast}</div>
        )}
      </section>
    </main>
  )
}

function TakeAssessmentGateway() {
  const token = typeof window !== 'undefined'
    ? new URLSearchParams(window.location.search).get('token')
    : null
  const [state, setState] = useState('loading')
  const [invite, setInvite] = useState(null)
  const [assessmentData, setAssessmentData] = useState(null)
  const [message, setMessage] = useState('')

  useEffect(() => {
    async function verify() {
      if (!token) {
        setState('invalid')
        return
      }
      try {
        const response = await fetch(`${apiUrl('/api/invite/verify')}?token=${encodeURIComponent(token)}`)
        if (!response.ok) {
          setState('invalid')
          return
        }
        const payload = await response.json()
        if (payload.expired) {
          setInvite(payload.invite || null)
          setState('expired')
          return
        }
        if (payload.taken) {
          setInvite(payload.invite || null)
          setState('taken')
          return
        }
        if (!payload.valid) {
          setState('invalid')
          return
        }
        setInvite(payload.invite || null)
        const assessmentId = payload.invite?.assessmentId || 'default'
        const assessmentRes = await fetch(apiUrl(`/api/public/assessment/${assessmentId}`))
        if (!assessmentRes.ok) {
          setState('invalid')
          return
        }
        const assessmentPayload = await assessmentRes.json()
        setAssessmentData(assessmentPayload)
        setState('ready')
      } catch {
        setState('invalid')
      }
    }
    verify()
  }, [token])

  async function resend() {
    try {
      await fetch(apiUrl('/api/invite/resend'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: invite?.email || '',
          assessmentId: invite?.assessmentId || null,
        }),
      })
      setState('resent')
      setMessage('A new link has been sent to your email.')
    } catch {
      setMessage('Failed to resend. Please contact your recruiter.')
    }
  }

  if (state === 'ready' && assessmentData) {
    return (
      <Assessment
        assessmentId={assessmentData.id}
        assessmentTitle={assessmentData.title}
        company={null}
        inviteToken={token}
      />
    )
  }

  return (
    <main className="page">
      <section className="card">
        <p className="eyebrow">InterviewOS Candidate</p>
        {state === 'loading' && <h1>Verifying invite...</h1>}
        {state === 'invalid' && (
          <>
            <h1>Invalid or missing link</h1>
            <p className="subtitle">Please check your invitation email or contact your recruiter.</p>
          </>
        )}
        {state === 'expired' && (
          <>
            <h1>This link has expired</h1>
            <p className="subtitle">Your assessment link expired. Request a new one.</p>
            <button type="button" onClick={resend}>Send New Link</button>
          </>
        )}
        {state === 'taken' && (
          <>
            <h1>Assessment already started</h1>
            <p className="subtitle">This assessment link has already been used.</p>
          </>
        )}
        {state === 'resent' && (
          <>
            <h1>New link sent</h1>
            <p className="subtitle">{message}</p>
          </>
        )}
      </section>
    </main>
  )
}

function LoadingPlaceholder({ assessmentId }) {
  const reportUrl = `/report/${assessmentId}`

  return (
    <main className="page">
      <section className="card">
        <p className="eyebrow">InterviewOS Candidate</p>
        <h1>Submission Received</h1>
        <p className="subtitle">Assessment {assessmentId} submission was uploaded. Your report is being generated.</p>
        <p className="subtitle">Open the report here in a few moments: <code>{reportUrl}</code></p>
        <div className="actions-row">
          <button type="button" onClick={() => navigateTo(reportUrl)}>Open Report</button>
          <button type="button" className="secondary" onClick={() => navigateTo('/dashboard')}>Back to Dashboard</button>
        </div>
      </section>
    </main>
  )
}
