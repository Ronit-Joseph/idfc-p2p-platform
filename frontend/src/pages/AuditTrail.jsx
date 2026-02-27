import { useEffect, useState } from 'react'
import { getAuditLogs, getAuditSummary, exportCSV } from '../api'
import { ScrollText, Activity, Shield, Clock, RefreshCw, Search, Download } from 'lucide-react'

const MODULE_COLOR = {
  workflow:      'bg-purple-100 text-purple-800',
  matching:      'bg-blue-100 text-blue-800',
  payments:      'bg-green-100 text-green-800',
  tds:           'bg-red-100 text-red-800',
  documents:     'bg-yellow-100 text-yellow-800',
  notifications: 'bg-orange-100 text-orange-800',
  invoices:      'bg-indigo-100 text-indigo-800',
  purchase_requests: 'bg-pink-100 text-pink-800',
  purchase_orders: 'bg-cyan-100 text-cyan-800',
  suppliers:     'bg-emerald-100 text-emerald-800',
}

const EVENT_ICON = {
  'approval.requested':   '📋',
  'approval.approved':    '✅',
  'approval.rejected':    '❌',
  'match.completed':      '🔗',
  'match.exception':      '⚡',
  'exception.resolved':   '✓',
  'payment_run.created':  '💳',
  'payment_run.processed':'💰',
  'tds.deducted':         '🧾',
  'document.uploaded':    '📄',
  'notification.created': '🔔',
}

export default function AuditTrail() {
  const [logs, setLogs] = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ source_module: '', event_type: '' })
  const [searchEntity, setSearchEntity] = useState('')

  const load = () => {
    setLoading(true)
    const params = {}
    if (filters.source_module) params.source_module = filters.source_module
    if (filters.event_type) params.event_type = filters.event_type
    Promise.all([getAuditLogs(params), getAuditSummary()])
      .then(([l, s]) => { setLogs(l); setSummary(s); setLoading(false) })
      .catch(() => setLoading(false))
  }

  useEffect(load, [filters.source_module, filters.event_type])

  const modules = summary ? Object.keys(summary.by_module || {}) : []
  const eventTypes = summary ? Object.keys(summary.by_event_type || {}) : []

  const filtered = searchEntity
    ? logs.filter(l => (l.entity_id || '').toLowerCase().includes(searchEntity.toLowerCase()) || (l.entity_type || '').toLowerCase().includes(searchEntity.toLowerCase()))
    : logs

  if (loading && logs.length === 0) return <div className="flex items-center justify-center h-64 text-warmgray-400">Loading audit trail…</div>

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-warmgray-900">Audit Trail</h1>
          <p className="text-sm text-warmgray-500 mt-0.5">Immutable event log · 7-year retention (RBI) · All system events auto-captured via event bus</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => exportCSV('audit')} className="btn-secondary flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium"><Download className="w-3.5 h-3.5" />Export CSV</button>
          <button onClick={load} className="btn-secondary text-xs">
            <RefreshCw className="w-3.5 h-3.5" /> Refresh
          </button>
        </div>
      </div>

      {/* Summary */}
      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl border border-brand-100 p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-warmgray-500 font-medium uppercase tracking-wide">Total Events</p>
                <p className="text-2xl font-bold text-warmgray-900 mt-1">{summary.total_events}</p>
              </div>
              <div className="bg-brand-50 p-2.5 rounded-lg"><ScrollText className="w-5 h-5 text-brand-600" /></div>
            </div>
          </div>
          <div className="bg-white rounded-xl border border-green-100 p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-warmgray-500 font-medium uppercase tracking-wide">Last 24 Hours</p>
                <p className="text-2xl font-bold text-warmgray-900 mt-1">{summary.recent_24h}</p>
              </div>
              <div className="bg-green-50 p-2.5 rounded-lg"><Clock className="w-5 h-5 text-green-600" /></div>
            </div>
          </div>
          <div className="bg-white rounded-xl border border-purple-100 p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-warmgray-500 font-medium uppercase tracking-wide">Active Modules</p>
                <p className="text-2xl font-bold text-warmgray-900 mt-1">{Object.keys(summary.by_module || {}).length}</p>
              </div>
              <div className="bg-purple-50 p-2.5 rounded-lg"><Activity className="w-5 h-5 text-purple-600" /></div>
            </div>
          </div>
          <div className="bg-white rounded-xl border border-yellow-100 p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-warmgray-500 font-medium uppercase tracking-wide">Event Types</p>
                <p className="text-2xl font-bold text-warmgray-900 mt-1">{Object.keys(summary.by_event_type || {}).length}</p>
              </div>
              <div className="bg-yellow-50 p-2.5 rounded-lg"><Shield className="w-5 h-5 text-yellow-600" /></div>
            </div>
          </div>
        </div>
      )}

      {/* Module breakdown */}
      {summary && summary.by_module && (
        <div className="card">
          <h3 className="text-sm font-semibold text-warmgray-700 mb-3">Events by Module</h3>
          <div className="flex gap-2 flex-wrap">
            {Object.entries(summary.by_module).map(([mod, count]) => (
              <button key={mod}
                onClick={() => setFilters(f => ({ ...f, source_module: f.source_module === mod ? '' : mod }))}
                className={`rounded-lg px-3 py-1.5 text-xs font-medium border transition-colors cursor-pointer ${
                  filters.source_module === mod ? 'ring-2 ring-brand-500 ring-offset-1' : ''
                } ${MODULE_COLOR[mod] || 'bg-warmgray-100 text-warmgray-800'}`}>
                {mod}: {count}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-3 items-center flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-warmgray-400" />
          <input
            type="text"
            placeholder="Search entity ID or type…"
            className="w-full pl-9 pr-3 py-2 text-sm border border-warmgray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
            value={searchEntity}
            onChange={e => setSearchEntity(e.target.value)}
          />
        </div>
        {filters.source_module && (
          <span className="badge badge-blue text-xs flex items-center gap-1">
            Module: {filters.source_module}
            <button onClick={() => setFilters(f => ({ ...f, source_module: '' }))} className="ml-1 hover:text-red-500">&times;</button>
          </span>
        )}
      </div>

      {/* Log table */}
      <div className="card p-0 overflow-hidden">
        <div className="table-wrapper">
          <table className="w-full text-sm">
            <thead className="bg-warmgray-50 border-b border-warmgray-100">
              <tr>
                {['', 'Event Type', 'Module', 'Entity', 'Entity ID', 'Actor', 'Timestamp'].map(h => (
                  <th key={h} className="px-3 py-3 text-left text-xs font-semibold text-warmgray-500 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-warmgray-50">
              {filtered.length === 0 ? (
                <tr><td colSpan={7} className="px-3 py-8 text-center text-warmgray-400 text-sm">No audit events found</td></tr>
              ) : filtered.map(log => (
                <tr key={log.id} className="table-row-hover">
                  <td className="px-3 py-3 text-base">{EVENT_ICON[log.event_type] || '📝'}</td>
                  <td className="px-3 py-3">
                    <span className="font-mono text-xs text-brand-700 font-medium">{log.event_type}</span>
                  </td>
                  <td className="px-3 py-3">
                    <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${MODULE_COLOR[log.source_module] || 'bg-warmgray-100 text-warmgray-800'}`}>
                      {log.source_module}
                    </span>
                  </td>
                  <td className="px-3 py-3 text-xs text-warmgray-600">{log.entity_type || '—'}</td>
                  <td className="px-3 py-3 font-mono text-xs text-warmgray-700">{log.entity_id || '—'}</td>
                  <td className="px-3 py-3 text-xs text-warmgray-500">{log.actor || 'System'}</td>
                  <td className="px-3 py-3 text-xs text-warmgray-400">
                    {log.timestamp ? new Date(log.timestamp).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
