import { useEffect, useMemo, useState } from 'react'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function apiUrl(path) {
  if (!path) return ''
  if (/^https?:\/\//.test(path)) return path
  return `${API_BASE_URL.replace(/\/$/, '')}${path.startsWith('/') ? path : `/${path}`}`
}

function formatDuration(seconds) {
  if (!seconds || Number.isNaN(Number(seconds))) return 'N/A'
  const total = Math.max(0, Number(seconds))
  const mins = Math.floor(total / 60)
  const secs = Math.floor(total % 60)
  return `${mins}m ${secs}s`
}

function statusTone(status) {
  if (status === 'pass') return 'border-emerald-200 bg-emerald-50 text-emerald-800'
  if (status === 'partial') return 'border-amber-200 bg-amber-50 text-amber-800'
  return 'border-rose-200 bg-rose-50 text-rose-800'
}

function asArray(value) {
  return Array.isArray(value) ? value : []
}

function ScoreRing({ score }) {
  const safeScore = typeof score === 'number' ? Math.max(0, Math.min(100, score)) : null
  const radius = 54
  const circumference = 2 * Math.PI * radius
  const dash = safeScore == null ? 0 : circumference * (safeScore / 100)
  return (
    <div className="relative h-36 w-36">
      <svg viewBox="0 0 128 128" className="h-full w-full -rotate-90">
        <circle cx="64" cy="64" r={radius} fill="none" stroke="rgba(15,23,42,0.10)" strokeWidth="10" />
        <circle
          cx="64"
          cy="64"
          r={radius}
          fill="none"
          stroke="rgb(15,23,42)"
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={`${dash} ${circumference - dash}`}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-semibold tracking-tight">{safeScore == null ? '--' : `${Math.round(safeScore)}%`}</span>
        <span className="text-xs uppercase tracking-[0.18em] text-gray-500">Score</span>
      </div>
    </div>
  )
}

function MetricCard({ label, value, hint }) {
  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
      <p className="text-xs uppercase tracking-[0.16em] text-gray-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold tracking-tight">{value ?? 'N/A'}</p>
      {hint && <p className="mt-1 text-sm text-gray-600">{hint}</p>}
    </div>
  )
}

function AssessmentOverview({ questionData }) {
  if (!questionData) return null
  return (
    <section className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
      <p className="text-xs uppercase tracking-[0.16em] text-gray-500">Assessment</p>
      <h2 className="mt-2 text-2xl font-semibold tracking-tight">{questionData.title}</h2>
      <p className="mt-2 max-w-4xl text-sm leading-6 text-gray-700">{questionData.overview || questionData.summary}</p>
      {asArray(questionData.tasks).length > 0 && (
        <div className="mt-5 grid gap-3 md:grid-cols-3">
          {questionData.tasks.map((task, index) => (
            <div key={`${task.title || index}`} className="rounded-2xl border border-gray-100 bg-gray-50 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-gray-500">Task {index + 1}</p>
              <p className="mt-1 font-semibold text-gray-950">{task.title}</p>
              <p className="mt-1 text-sm text-gray-600">{task.description}</p>
            </div>
          ))}
        </div>
      )}
      {asArray(questionData.skillsTested).length > 0 && (
        <div className="mt-5 flex flex-wrap gap-2">
          {questionData.skillsTested.map((skill) => (
            <span key={skill} className="rounded-full border border-gray-200 bg-white px-3 py-1 text-xs font-semibold text-gray-700">{skill}</span>
          ))}
        </div>
      )}
    </section>
  )
}

function TestCases({ results }) {
  const rows = asArray(results)
  return (
    <section className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between gap-4">
        <h2 className="text-xl font-semibold tracking-tight">Evaluation Checks</h2>
        <span className="text-sm text-gray-500">{rows.length} checks</span>
      </div>
      <div className="mt-5 space-y-4">
        {rows.map((item, index) => (
          <article key={`${item.name || 'check'}-${index}`} className="rounded-2xl border border-gray-100 bg-gray-50 p-4">
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <p className="font-semibold text-gray-950">{item.name || `Check ${index + 1}`}</p>
                {item.score !== undefined && <p className="mt-1 text-sm text-gray-500">Score: {item.score}/{item.maxScore || 10}</p>}
              </div>
              <span className={`inline-flex w-fit rounded-full border px-3 py-1 text-xs font-semibold ${statusTone(item.status)}`}>{item.status || 'unknown'}</span>
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <div className="rounded-xl border border-gray-200 bg-white p-3">
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-gray-500">Expected</p>
                <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap text-xs leading-5 text-gray-700">{String(item.summary?.expected || item.expected || '-')}</pre>
              </div>
              <div className="rounded-xl border border-gray-200 bg-white p-3">
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-gray-500">Observed</p>
                <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap text-xs leading-5 text-gray-700">{String(item.summary?.output || item.output || '-')}</pre>
              </div>
            </div>
          </article>
        ))}
        {rows.length === 0 && <p className="text-sm text-gray-600">No evaluation checks available yet.</p>}
      </div>
    </section>
  )
}

function DiffViewer({ diffs }) {
  const rows = asArray(diffs).slice(0, 8)
  if (rows.length === 0) return null
  return (
    <section className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
      <h2 className="text-xl font-semibold tracking-tight">Code and Artifact Diffs</h2>
      <div className="mt-5 space-y-4">
        {rows.map((diff, index) => (
          <details key={`${diff.path}-${index}`} className="overflow-hidden rounded-2xl border border-gray-200 bg-gray-50" open={index === 0}>
            <summary className="cursor-pointer px-4 py-3 font-semibold text-gray-950">{diff.path || `Diff ${index + 1}`}</summary>
            <div className="grid border-t border-gray-200 md:grid-cols-2">
              <div className="border-b border-gray-200 bg-white p-3 md:border-b-0 md:border-r">
                <p className="mb-2 text-xs font-semibold uppercase tracking-[0.14em] text-rose-600">Original</p>
                <pre className="max-h-96 overflow-auto whitespace-pre-wrap text-xs leading-5 text-gray-700">{diff.original || ''}</pre>
              </div>
              <div className="bg-white p-3">
                <p className="mb-2 text-xs font-semibold uppercase tracking-[0.14em] text-emerald-700">Submitted</p>
                <pre className="max-h-96 overflow-auto whitespace-pre-wrap text-xs leading-5 text-gray-700">{diff.modified || ''}</pre>
              </div>
            </div>
          </details>
        ))}
      </div>
    </section>
  )
}

function CodeQuality({ eslintIssues }) {
  const files = asArray(eslintIssues)
  const issues = files.flatMap((file) => asArray(file.messages).map((msg) => ({ ...msg, file: file.file })))
  if (issues.length === 0) return null
  return (
    <section className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
      <h2 className="text-xl font-semibold tracking-tight">Code Quality Review</h2>
      <div className="mt-5 space-y-3">
        {issues.map((issue, index) => (
          <div key={`${issue.file}-${issue.line}-${index}`} className="rounded-2xl border border-gray-100 bg-gray-50 p-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className={`rounded-full px-2 py-1 text-xs font-semibold ${issue.severity === 2 ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'}`}>{issue.severity === 2 ? 'Error' : 'Warning'}</span>
              <span className="text-sm font-semibold text-gray-950">{issue.file}</span>
              {issue.line && <span className="text-xs text-gray-500">Line {issue.line}</span>}
            </div>
            <p className="mt-2 text-sm text-gray-700">{issue.message}</p>
            {issue.codeLine && <pre className="mt-3 overflow-auto rounded-xl bg-white p-3 text-xs text-gray-800">{issue.codeLine}</pre>}
          </div>
        ))}
      </div>
    </section>
  )
}

function AppUsage({ appUsage, totalDuration }) {
  const rows = asArray(appUsage)
  return (
    <section className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
      <h2 className="text-xl font-semibold tracking-tight">Screen Usage</h2>
      <p className="mt-1 text-sm text-gray-600">Total duration: {formatDuration(totalDuration)}</p>
      <div className="mt-5 space-y-3">
        {rows.map((entry, index) => {
          const duration = Number(entry.duration || entry.time || 0)
          const pct = totalDuration ? Math.round((duration / Number(totalDuration)) * 100) : 0
          return (
            <div key={`${entry.name}-${index}`}>
              <div className="flex justify-between text-sm">
                <span className="font-medium text-gray-900">{entry.name}</span>
                <span className="text-gray-600">{formatDuration(duration)}{pct ? ` · ${pct}%` : ''}</span>
              </div>
              <div className="mt-2 h-3 overflow-hidden rounded-full bg-gray-100">
                <div className="h-full rounded-full bg-gray-950" style={{ width: `${Math.max(pct, rows.length ? 3 : 0)}%` }} />
              </div>
            </div>
          )
        })}
        {rows.length === 0 && <p className="text-sm text-gray-600">No screen telemetry found yet.</p>}
      </div>
    </section>
  )
}

function Artifacts({ report }) {
  const assessmentVideoUrl = report.assessmentVideoUrl || (report.assessmentRecordingKey ? `/api/artifacts/recordings/${report.id}/assessment` : '')
  const reflectionVideoUrl = report.reflectionVideoUrl || (report.reflectionRecordingKey ? `/api/artifacts/recordings/${report.id}/reflection` : '')
  return (
    <section className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-xl font-semibold tracking-tight">Artifacts</h2>
          <p className="mt-1 text-sm text-gray-600">Submission, workflow recording, and reflection evidence.</p>
        </div>
        <a className="inline-flex w-fit rounded-full bg-gray-950 px-4 py-2 text-sm font-semibold text-white" href={apiUrl(report.submissionDownloadUrl || `/api/artifacts/submissions/${report.id}`)}>
          Download Submission
        </a>
      </div>
      <div className="mt-5 grid gap-5 md:grid-cols-2">
        <div className="rounded-2xl border border-gray-100 bg-gray-50 p-4">
          <p className="mb-3 text-sm font-semibold text-gray-950">Assessment Recording</p>
          {assessmentVideoUrl ? <video controls className="w-full rounded-xl bg-black" src={apiUrl(assessmentVideoUrl)} /> : <p className="text-sm text-gray-600">No assessment recording found.</p>}
        </div>
        <div className="rounded-2xl border border-gray-100 bg-gray-50 p-4">
          <p className="mb-3 text-sm font-semibold text-gray-950">Reflection Recording</p>
          {reflectionVideoUrl ? <video controls className="w-full rounded-xl bg-black" src={apiUrl(reflectionVideoUrl)} /> : <p className="text-sm text-gray-600">No reflection recording found.</p>}
        </div>
      </div>
    </section>
  )
}

function Assessment4Metrics({ data }) {
  if (!data) return null
  return (
    <section className="grid gap-4 md:grid-cols-3">
      <MetricCard label="ID Macro F1" value={data.id_macro_f1 == null ? 'N/A' : `${Math.round(data.id_macro_f1 * 100)}%`} />
      <MetricCard label="OOD Macro F1" value={data.ood_macro_f1 == null ? 'N/A' : `${Math.round(data.ood_macro_f1 * 100)}%`} />
      <MetricCard label="Latency" value={data.latency_sec == null ? 'N/A' : `${Math.round(data.latency_sec * 1000)}ms`} />
    </section>
  )
}

export default function ReportPage({ reportId }) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [report, setReport] = useState(null)

  const endpoint = useMemo(() => apiUrl(`/report/${encodeURIComponent(String(reportId || ''))}`), [reportId])

  useEffect(() => {
    let cancelled = false
    let timer = null

    async function loadReport() {
      if (!reportId) {
        setError('Missing report id.')
        setLoading(false)
        return
      }

      setLoading(true)
      setError('')
      try {
        const response = await fetch(endpoint)
        if (!response.ok) {
          const payload = await response.json().catch(() => ({}))
          throw new Error(payload.detail || payload.error || 'Failed to load report')
        }
        const payload = await response.json()
        if (cancelled) return
        setReport(payload)
        if (!payload.reportReady) {
          timer = window.setTimeout(loadReport, 3000)
        }
      } catch (loadError) {
        if (!cancelled) setError(loadError.message || 'Failed to load report')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    loadReport()
    return () => {
      cancelled = true
      if (timer) window.clearTimeout(timer)
    }
  }, [endpoint, reportId])

  return (
    <div className="min-h-screen bg-[radial-gradient(1000px_560px_at_50%_-200px,rgba(15,23,42,0.13),rgba(255,255,255,0)),linear-gradient(180deg,#fff_0%,#f7f7f5_55%,#ececea_100%)] text-gray-950">
      <main className="mx-auto w-full max-w-7xl px-5 py-10 md:px-8">
        <header className="mb-8 flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-gray-500">InterviewOS Report</p>
            <h1 className="mt-2 text-4xl font-semibold tracking-tight">Candidate Assessment Report</h1>
            <p className="mt-2 text-sm text-gray-600">Report ID: {reportId || 'N/A'}</p>
          </div>
          {report && <span className={`w-fit rounded-full border px-4 py-2 text-sm font-semibold ${report.reportReady ? 'border-emerald-200 bg-emerald-50 text-emerald-800' : 'border-amber-200 bg-amber-50 text-amber-900'}`}>{report.reportReady ? 'Ready' : 'Processing'}</span>}
        </header>

        {loading && (
          <section className="rounded-3xl border border-gray-200 bg-white p-8 shadow-sm">
            <p className="text-base text-gray-700">Loading report...</p>
          </section>
        )}

        {!loading && error && (
          <section className="rounded-3xl border border-rose-200 bg-rose-50 p-8 shadow-sm">
            <p className="text-base font-medium text-rose-700">{error}</p>
          </section>
        )}

        {!loading && !error && report && (
          <div className="space-y-6">
            {!report.reportReady && (
              <section className="rounded-3xl border border-amber-200 bg-amber-50 p-5 shadow-sm">
                <p className="text-sm font-medium text-amber-900">Report generation is in progress. This page auto-refreshes every few seconds.</p>
              </section>
            )}
            {report.error && (
              <section className="rounded-3xl border border-amber-200 bg-amber-50 p-5 shadow-sm">
                <p className="text-sm font-medium text-amber-900">{report.error}</p>
              </section>
            )}

            <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
              <div className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
                <p className="text-xs uppercase tracking-[0.16em] text-gray-500">Candidate</p>
                <h2 className="mt-2 text-3xl font-semibold tracking-tight">{report.name || 'Candidate'}</h2>
                <p className="mt-1 text-sm text-gray-600">{report.email || '-'}</p>
                <p className="mt-4 text-sm text-gray-700"><span className="font-semibold">Assessment:</span> {report.assessmentTitle || '-'}</p>
                <p className="mt-1 text-sm text-gray-700"><span className="font-semibold">Type:</span> {report.assessmentType || '-'}</p>
              </div>
              <div className="grid gap-4 rounded-3xl border border-gray-200 bg-white p-6 shadow-sm md:grid-cols-[auto_1fr] md:items-center">
                <ScoreRing score={report.score} />
                <div className="grid gap-4">
                  <MetricCard label="Code Quality" value={report.codeQuality == null ? 'N/A' : `${report.codeQuality}%`} />
                  <MetricCard label="Duration" value={formatDuration(report.totalDuration)} />
                </div>
              </div>
            </section>

            <AssessmentOverview questionData={report.questionData} />
            <Assessment4Metrics data={report.assessment4Results} />
            <TestCases results={report.results} />
            <CodeQuality eslintIssues={report.eslintIssues} />
            <section className="grid gap-6 lg:grid-cols-2">
              <AppUsage appUsage={report.appUsage} totalDuration={report.totalDuration} />
              <section className="rounded-3xl border border-gray-200 bg-white p-6 shadow-sm">
                <h2 className="text-xl font-semibold tracking-tight">Workflow Summary</h2>
                <ul className="mt-4 list-disc space-y-2 pl-5 text-sm leading-6 text-gray-700">
                  {asArray(report.codeSummaryBullets).map((bullet, index) => <li key={`${index}-${bullet}`}>{bullet}</li>)}
                  {asArray(report.codeSummaryBullets).length === 0 && <li>No summary available yet.</li>}
                </ul>
              </section>
            </section>
            <DiffViewer diffs={report.diffs} />
            <Artifacts report={report} />
          </div>
        )}
      </main>
    </div>
  )
}
