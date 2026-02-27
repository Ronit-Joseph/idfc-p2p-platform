import { useEffect, useState } from 'react'
import { getMatchResults, getMatchSummary, getMatchExceptions, resolveMatchException } from '../api'
import { Scale, CheckCircle, AlertTriangle, XCircle, RefreshCw, Shield } from 'lucide-react'

const fmtInr = v => {
  if (!v && v !== 0) return '—'
  if (v >= 100000) return `₹${(v/100000).toFixed(2)}L`
  return `₹${v?.toLocaleString('en-IN') ?? '—'}`
}

const MATCH_BADGE = {
  PASSED:     'badge badge-green',
  EXCEPTION:  'badge badge-yellow',
  FAILED:     'badge badge-red',
  PENDING:    'badge badge-gray',
}

const MATCH_TYPE_BADGE = {
  '2WAY': 'bg-blue-100 text-blue-800',
  '3WAY': 'bg-purple-100 text-purple-800',
}

const EXCEPTION_SEVERITY = {
  CRITICAL: 'bg-red-50 border-red-200 text-red-800',
  HIGH:     'bg-orange-50 border-orange-200 text-orange-800',
  MEDIUM:   'bg-yellow-50 border-yellow-200 text-yellow-800',
  LOW:      'bg-blue-50 border-blue-200 text-blue-800',
}

const RESOLUTION_BADGE = {
  APPROVED_OVERRIDE: 'badge badge-green',
  REJECTED:          'badge badge-red',
  ESCALATED:         'badge badge-purple',
  null:              'badge badge-yellow',
}

export default function Matching() {
  const [results, setResults] = useState([])
  const [exceptions, setExceptions] = useState([])
  const [summary, setSummary] = useState(null)
  const [tab, setTab] = useState('results')
  const [loading, setLoading] = useState(true)
  const [resolving, setResolving] = useState(null)

  const load = () => {
    setLoading(true)
    Promise.all([getMatchResults(), getMatchSummary(), getMatchExceptions()])
      .then(([r, s, e]) => { setResults(r); setSummary(s); setExceptions(e); setLoading(false) })
      .catch(() => setLoading(false))
  }

  useEffect(load, [])

  const handleResolve = async (exId, resolution) => {
    setResolving(exId)
    try {
      await resolveMatchException(exId, { resolution, resolved_by: 'Priya Menon' })
      load()
    } finally {
      setResolving(null)
    }
  }

  if (loading) return <div className="flex items-center justify-center h-64 text-warmgray-400">Loading matching data…</div>

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-warmgray-900">Invoice Matching Engine</h1>
          <p className="text-sm text-warmgray-500 mt-0.5">2-Way (PO vs Invoice) & 3-Way (PO vs GRN vs Invoice) matching · 5% tolerance · Fraud detection</p>
        </div>
        <button onClick={load} className="btn-secondary text-xs">
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </button>
      </div>

      {/* Summary cards */}
      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="bg-white rounded-xl border border-brand-100 p-5">
            <p className="text-xs text-warmgray-500 font-medium uppercase tracking-wide">Total Matches</p>
            <p className="text-2xl font-bold text-warmgray-900 mt-1">{summary.total_matches}</p>
          </div>
          <div className="bg-white rounded-xl border border-green-100 p-5">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              <p className="text-xs text-warmgray-500 font-medium uppercase tracking-wide">Passed</p>
            </div>
            <p className="text-2xl font-bold text-green-700 mt-1">{summary.passed || 0}</p>
          </div>
          <div className="bg-white rounded-xl border border-yellow-100 p-5">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-yellow-500" />
              <p className="text-xs text-warmgray-500 font-medium uppercase tracking-wide">Exception</p>
            </div>
            <p className="text-2xl font-bold text-yellow-700 mt-1">{summary.exceptions || 0}</p>
          </div>
          <div className="bg-white rounded-xl border border-red-100 p-5">
            <div className="flex items-center gap-2">
              <XCircle className="w-4 h-4 text-red-500" />
              <p className="text-xs text-warmgray-500 font-medium uppercase tracking-wide">Failed</p>
            </div>
            <p className="text-2xl font-bold text-red-700 mt-1">{summary.blocked_fraud || 0}</p>
          </div>
          <div className="bg-white rounded-xl border border-orange-100 p-5">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-orange-500" />
              <p className="text-xs text-warmgray-500 font-medium uppercase tracking-wide">Open Exceptions</p>
            </div>
            <p className="text-2xl font-bold text-orange-700 mt-1">{summary.open_exceptions}</p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2">
        {[['results', 'Match Results'], ['exceptions', `Exceptions (${exceptions.length})`]].map(([k, l]) => (
          <button key={k}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${tab === k ? 'bg-brand-500 text-white' : 'bg-white text-warmgray-600 border border-warmgray-200 hover:bg-warmgray-50'}`}
            onClick={() => setTab(k)}>{l}
          </button>
        ))}
      </div>

      {tab === 'results' ? (
        <div className="card p-0 overflow-hidden">
          <div className="table-wrapper">
          <table className="w-full text-sm">
            <thead className="bg-warmgray-50 border-b border-warmgray-100">
              <tr>
                {['Invoice', 'Supplier', 'Type', 'Variance', 'Status', 'Note', 'Date'].map(h => (
                  <th key={h} className="px-3 py-3 text-left text-xs font-semibold text-warmgray-500 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-warmgray-50">
              {results.length === 0 ? (
                <tr><td colSpan={7} className="px-3 py-8 text-center text-warmgray-400 text-sm">No match results yet</td></tr>
              ) : results.map(r => (
                <tr key={r.id} className="table-row-hover">
                  <td className="px-3 py-3 font-mono text-xs text-brand-700 font-medium">{r.invoice_number}</td>
                  <td className="px-3 py-3 text-xs text-warmgray-700">{r.supplier_name || '—'}</td>
                  <td className="px-3 py-3">
                    <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${MATCH_TYPE_BADGE[r.match_type] || 'bg-warmgray-100'}`}>
                      {r.match_type}
                    </span>
                  </td>
                  <td className="px-3 py-3">
                    <span className={`font-medium ${r.variance_pct > 5 ? 'text-red-600' : r.variance_pct > 0 ? 'text-yellow-600' : 'text-green-600'}`}>
                      {r.variance_pct != null ? `${r.variance_pct.toFixed(1)}%` : '—'}
                    </span>
                  </td>
                  <td className="px-3 py-3"><span className={MATCH_BADGE[r.status] || 'badge badge-gray'}>{r.status}</span></td>
                  <td className="px-3 py-3 text-xs text-warmgray-500">{r.note || r.exception_reason || '—'}</td>
                  <td className="px-3 py-3 text-xs text-warmgray-400">{r.created_at ? new Date(r.created_at).toLocaleDateString('en-IN') : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {exceptions.length === 0 ? (
            <div className="card text-center text-warmgray-400 py-12">
              <CheckCircle className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm">No matching exceptions</p>
            </div>
          ) : exceptions.map(ex => (
            <div key={ex.id} className={`rounded-xl border p-4 ${EXCEPTION_SEVERITY[ex.severity] || 'bg-warmgray-50 border-warmgray-200'}`}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-medium">{ex.invoice_id}</span>
                    <span className="text-xs font-bold uppercase">{ex.severity}</span>
                    <span className="text-xs">{ex.exception_type?.replace(/_/g, ' ')}</span>
                  </div>
                  {ex.resolved_by && <div className="text-xs mt-1 opacity-70">Resolved by {ex.resolved_by}</div>}
                </div>
                <div className="flex items-center gap-2">
                  {ex.resolution ? (
                    <span className={RESOLUTION_BADGE[ex.resolution] || 'badge badge-gray'}>{ex.resolution?.replace(/_/g, ' ')}</span>
                  ) : (
                    <>
                      <button
                        onClick={() => handleResolve(ex.id, 'APPROVED_OVERRIDE')}
                        disabled={resolving === ex.id}
                        className="px-3 py-1.5 bg-green-600 text-white rounded-lg text-xs font-medium hover:bg-green-700 disabled:opacity-50">
                        Override
                      </button>
                      <button
                        onClick={() => handleResolve(ex.id, 'REJECTED')}
                        disabled={resolving === ex.id}
                        className="px-3 py-1.5 bg-red-600 text-white rounded-lg text-xs font-medium hover:bg-red-700 disabled:opacity-50">
                        Reject
                      </button>
                      <button
                        onClick={() => handleResolve(ex.id, 'ESCALATED')}
                        disabled={resolving === ex.id}
                        className="px-3 py-1.5 bg-purple-600 text-white rounded-lg text-xs font-medium hover:bg-purple-700 disabled:opacity-50">
                        Escalate
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
