import { useEffect, useMemo, useState } from 'react'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function apiUrl(path) {
  return `${API_BASE_URL.replace(/\/$/, '')}${path}`
}

function formatDuration(seconds) {
  if (!seconds || Number.isNaN(Number(seconds))) return 'N/A'
  const total = Math.max(0, Number(seconds))
  const mins = Math.floor(total / 60)
  const secs = Math.floor(total % 60)
  return `${mins}m ${secs}s`
}

function statusBadge(status) {
  if (status === 'pass') return 'bg-emerald-100 text-emerald-800'
  if (status === 'partial') return 'bg-amber-100 text-amber-800'
  return 'bg-red-100 text-red-800'
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
        if (cancelled) {
          return
        }
        setReport(payload)
        if (!payload.reportReady) {
          timer = window.setTimeout(loadReport, 3000)
        }
      } catch (loadError) {
        setError(loadError.message || 'Failed to load report')
      } finally {
        setLoading(false)
      }
    }

    loadReport()
    return () => {
      cancelled = true
      if (timer) {
        window.clearTimeout(timer)
      }
    }
  }, [endpoint, reportId])

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-100 text-gray-900">
      <main className="mx-auto w-full max-w-6xl px-6 py-12">
        <header className="mb-8">
          <p className="text-xs uppercase tracking-[0.16em] text-gray-500">InterviewOS Report</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">Candidate Assessment Report</h1>
          <p className="mt-2 text-sm text-gray-600">{reportId ? `Report ID: ${reportId}` : 'No report id provided'}</p>
        </header>

        {loading && (
          <section className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
            <p className="text-base text-gray-700">Loading report...</p>
          </section>
        )}

        {!loading && error && (
          <section className="rounded-2xl border border-red-200 bg-red-50 p-8 shadow-sm">
            <p className="text-base font-medium text-red-700">{error}</p>
          </section>
        )}

        {!loading && !error && report && (
          <div className="space-y-6">
            {!report.reportReady && (
              <section className="rounded-2xl border border-amber-200 bg-amber-50 p-5 shadow-sm">
                <p className="text-sm font-medium text-amber-900">Report generation is in progress. This page auto-refreshes every few seconds.</p>
              </section>
            )}
            <section className="grid gap-4 md:grid-cols-4">
              <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm md:col-span-2">
                <h2 className="text-sm font-semibold text-gray-500">Candidate</h2>
                <p className="mt-2 text-xl font-semibold">{report.name || '-'}</p>
                <p className="mt-1 text-sm text-gray-600">{report.email || '-'}</p>
                <p className="mt-1 text-sm text-gray-600">Assessment: {report.assessmentTitle || '-'}</p>
              </div>

              <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
                <h2 className="text-sm font-semibold text-gray-500">Score</h2>
                <p className="mt-2 text-3xl font-semibold">{report.score ?? 'N/A'}</p>
              </div>

              <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
                <h2 className="text-sm font-semibold text-gray-500">Code Quality</h2>
                <p className="mt-2 text-3xl font-semibold">{report.codeQuality ?? 'N/A'}</p>
              </div>
            </section>

            {report.error && (
              <section className="rounded-2xl border border-amber-200 bg-amber-50 p-5 shadow-sm">
                <p className="text-sm font-medium text-amber-800">{report.error}</p>
              </section>
            )}

            <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold tracking-tight">Evaluation Checks</h2>
              <div className="mt-4 overflow-x-auto">
                <table className="w-full border-collapse text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 text-left text-gray-600">
                      <th className="py-2 pr-3">Check</th>
                      <th className="py-2 pr-3">Status</th>
                      <th className="py-2 pr-3">Expected</th>
                      <th className="py-2">Observed</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(report.results || []).map((item, index) => (
                      <tr key={`${item.name}-${index}`} className="border-b border-gray-100 align-top">
                        <td className="py-3 pr-3 font-medium text-gray-900">{item.name}</td>
                        <td className="py-3 pr-3">
                          <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${statusBadge(item.status)}`}>
                            {item.status || 'unknown'}
                          </span>
                        </td>
                        <td className="py-3 pr-3 text-gray-600">{item.expected || '-'}</td>
                        <td className="py-3 text-gray-700">{item.output || '-'}</td>
                      </tr>
                    ))}
                    {(report.results || []).length === 0 && (
                      <tr>
                        <td className="py-4 text-gray-600" colSpan={4}>No checks available yet.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="grid gap-6 md:grid-cols-2">
              <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
                <h2 className="text-lg font-semibold tracking-tight">Workflow Summary</h2>
                <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-gray-700">
                  {(report.codeSummaryBullets || []).map((bullet, index) => (
                    <li key={`${index}-${bullet}`}>{bullet}</li>
                  ))}
                  {(report.codeSummaryBullets || []).length === 0 && <li>No summary available yet.</li>}
                </ul>
              </div>

              <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
                <h2 className="text-lg font-semibold tracking-tight">App Usage</h2>
                <p className="mt-2 text-sm text-gray-600">Total Duration: {formatDuration(report.totalDuration)}</p>
                <ul className="mt-3 space-y-2 text-sm text-gray-700">
                  {(report.appUsage || []).map((entry, index) => (
                    <li key={`${entry.name}-${index}`} className="flex items-center justify-between rounded-lg border border-gray-100 px-3 py-2">
                      <span>{entry.name}</span>
                      <span className="font-medium">{formatDuration(entry.duration)}</span>
                    </li>
                  ))}
                  {(report.appUsage || []).length === 0 && <li>No app usage telemetry found.</li>}
                </ul>
              </div>
            </section>

            <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold tracking-tight">Artifacts</h2>
              <div className="mt-3 grid gap-2 text-sm text-gray-700 md:grid-cols-3">
                <div className="rounded-lg border border-gray-100 p-3">
                  <p className="text-xs uppercase tracking-wide text-gray-500">Submission File</p>
                  <p className="mt-1 break-all">{report.submissionFile || 'Not available'}</p>
                </div>
                <div className="rounded-lg border border-gray-100 p-3">
                  <p className="text-xs uppercase tracking-wide text-gray-500">Assessment Recording</p>
                  <p className="mt-1 break-all">{report.assessmentRecordingKey || 'Not available'}</p>
                </div>
                <div className="rounded-lg border border-gray-100 p-3">
                  <p className="text-xs uppercase tracking-wide text-gray-500">Reflection Recording</p>
                  <p className="mt-1 break-all">{report.reflectionRecordingKey || 'Not available'}</p>
                </div>
              </div>
            </section>
          </div>
        )}
      </main>
    </div>
  )
}
