import { useState, useEffect } from 'react'
import { Search, Plus, Send, Award, Clock, FileText, Users, ChevronDown, ChevronUp, X } from 'lucide-react'
import api from '../api'

const STATUS_COLORS = {
  DRAFT: 'badge-gray',
  PUBLISHED: 'badge-blue',
  EVALUATION: 'badge-yellow',
  AWARDED: 'badge-green',
  CANCELLED: 'badge-red',
}

const RESP_STATUS_COLORS = {
  SUBMITTED: 'badge-blue',
  SHORTLISTED: 'badge-yellow',
  AWARDED: 'badge-green',
  REJECTED: 'badge-red',
}

function fmt(amount) {
  if (!amount) return '—'
  if (amount >= 10000000) return `₹${(amount / 10000000).toFixed(1)}Cr`
  if (amount >= 100000) return `₹${(amount / 100000).toFixed(1)}L`
  return `₹${amount.toLocaleString('en-IN')}`
}

export default function Sourcing() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('ALL')
  const [expandedId, setExpandedId] = useState(null)
  const [expandedDetail, setExpandedDetail] = useState(null)
  const [showForm, setShowForm] = useState(false)

  const load = () => {
    setLoading(true)
    api.get('/sourcing/rfqs').then(r => { setData(r.data); setLoading(false) }).catch(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const loadDetail = (rfqId) => {
    if (expandedId === rfqId) {
      setExpandedId(null)
      setExpandedDetail(null)
      return
    }
    setExpandedId(rfqId)
    api.get(`/sourcing/rfqs/${rfqId}`).then(r => setExpandedDetail(r.data)).catch(() => {})
  }

  if (loading || !data) return (
    <div className="flex items-center justify-center py-20 text-warmgray-400">
      <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  const { rfqs, summary } = data
  const filtered = filter === 'ALL' ? rfqs : rfqs.filter(r => r.status === filter)

  const stats = [
    { label: 'Total RFQs', value: summary.total, icon: FileText, color: 'text-brand-600 bg-brand-50' },
    { label: 'Published', value: summary.published, icon: Send, color: 'text-blue-600 bg-blue-50' },
    { label: 'In Evaluation', value: summary.evaluation, icon: Clock, color: 'text-amber-600 bg-amber-50' },
    { label: 'Awarded', value: summary.awarded, icon: Award, color: 'text-emerald-600 bg-emerald-50' },
  ]

  return (
    <div>
      <div className="page-header flex items-center justify-between">
        <div>
          <h1 className="page-title">Sourcing / RFQ</h1>
          <p className="page-subtitle">Manage requests for quotation and vendor selection</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium">
          <Plus className="w-4 h-4" /> New RFQ
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {stats.map(s => (
          <div key={s.label} className="stat-card">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${s.color}`}>
                <s.icon className="w-5 h-5" />
              </div>
              <div>
                <div className="text-2xl font-bold text-warmgray-800">{s.value}</div>
                <div className="text-xs text-warmgray-500">{s.label}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Create Form */}
      {showForm && <CreateRFQForm onClose={() => setShowForm(false)} onCreated={load} />}

      {/* Filters */}
      <div className="flex items-center gap-2 mb-4">
        {['ALL', 'DRAFT', 'PUBLISHED', 'EVALUATION', 'AWARDED'].map(f => (
          <button key={f} onClick={() => setFilter(f)} className={filter === f ? 'filter-pill filter-pill-active' : 'filter-pill filter-pill-inactive'}>
            {f === 'ALL' ? 'All' : f.charAt(0) + f.slice(1).toLowerCase()}
          </button>
        ))}
      </div>

      {/* RFQ Cards */}
      <div className="space-y-3">
        {filtered.map(rfq => (
          <div key={rfq.id} className="card p-0">
            <div className="px-5 py-4 flex items-center justify-between cursor-pointer table-row-hover rounded-xl" onClick={() => loadDetail(rfq.rfq_number)}>
              <div className="flex items-center gap-4 flex-1 min-w-0">
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 bg-brand-50 rounded-lg flex items-center justify-center">
                    <Search className="w-5 h-5 text-brand-600" />
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="font-medium text-warmgray-800">{rfq.rfq_number}</span>
                    <span className={`badge ${STATUS_COLORS[rfq.status] || 'badge-gray'}`}>{rfq.status}</span>
                  </div>
                  <div className="text-sm text-warmgray-600 truncate">{rfq.title}</div>
                </div>
              </div>
              <div className="flex items-center gap-6 text-sm">
                <div className="text-right hidden sm:block">
                  <div className="text-xs text-warmgray-400">Budget</div>
                  <div className="font-medium text-warmgray-800">{fmt(rfq.budget_estimate)}</div>
                </div>
                <div className="text-right hidden md:block">
                  <div className="text-xs text-warmgray-400">Responses</div>
                  <div className="font-medium text-warmgray-800 flex items-center gap-1"><Users className="w-3.5 h-3.5" />{rfq.response_count}</div>
                </div>
                <div className="text-right hidden md:block">
                  <div className="text-xs text-warmgray-400">Deadline</div>
                  <div className="text-warmgray-600">{rfq.submission_deadline || '—'}</div>
                </div>
                {expandedId === rfq.rfq_number ? <ChevronUp className="w-4 h-4 text-warmgray-400" /> : <ChevronDown className="w-4 h-4 text-warmgray-400" />}
              </div>
            </div>

            {/* Expanded detail — bid comparison */}
            {expandedId === rfq.rfq_number && expandedDetail && (
              <div className="px-5 pb-4 border-t border-warmgray-100">
                <div className="pt-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-semibold text-warmgray-700">Bid Comparison</h4>
                    {expandedDetail.evaluation_criteria && (
                      <span className="text-xs text-warmgray-400">Weighting: Technical 60% / Commercial 40%</span>
                    )}
                  </div>
                  {expandedDetail.responses && expandedDetail.responses.length > 0 ? (
                    <div className="table-wrapper">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-warmgray-100">
                            <th className="text-left px-3 py-2 text-xs font-medium uppercase tracking-wider text-warmgray-400">Supplier</th>
                            <th className="text-left px-3 py-2 text-xs font-medium uppercase tracking-wider text-warmgray-400">Quoted Amount</th>
                            <th className="text-left px-3 py-2 text-xs font-medium uppercase tracking-wider text-warmgray-400">Timeline</th>
                            <th className="text-left px-3 py-2 text-xs font-medium uppercase tracking-wider text-warmgray-400">Technical</th>
                            <th className="text-left px-3 py-2 text-xs font-medium uppercase tracking-wider text-warmgray-400">Commercial</th>
                            <th className="text-left px-3 py-2 text-xs font-medium uppercase tracking-wider text-warmgray-400">Total Score</th>
                            <th className="text-left px-3 py-2 text-xs font-medium uppercase tracking-wider text-warmgray-400">Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {expandedDetail.responses.map((r, i) => (
                            <tr key={r.id} className={`border-b border-warmgray-50 ${i === 0 ? 'bg-emerald-50/30' : ''}`}>
                              <td className="px-3 py-2.5 font-medium text-warmgray-800">{r.supplier_name}</td>
                              <td className="px-3 py-2.5 text-warmgray-700">{fmt(r.quoted_amount)}</td>
                              <td className="px-3 py-2.5 text-warmgray-600">{r.delivery_timeline || '—'}</td>
                              <td className="px-3 py-2.5">
                                <div className="flex items-center gap-2">
                                  <div className="w-16 h-1.5 bg-warmgray-100 rounded-full overflow-hidden">
                                    <div className="h-full bg-brand-500 rounded-full" style={{ width: `${r.technical_score || 0}%` }} />
                                  </div>
                                  <span className="text-xs text-warmgray-600">{r.technical_score || 0}</span>
                                </div>
                              </td>
                              <td className="px-3 py-2.5">
                                <div className="flex items-center gap-2">
                                  <div className="w-16 h-1.5 bg-warmgray-100 rounded-full overflow-hidden">
                                    <div className="h-full bg-brand-400 rounded-full" style={{ width: `${r.commercial_score || 0}%` }} />
                                  </div>
                                  <span className="text-xs text-warmgray-600">{r.commercial_score || 0}</span>
                                </div>
                              </td>
                              <td className="px-3 py-2.5">
                                <span className={`text-sm font-bold ${i === 0 ? 'text-emerald-600' : 'text-warmgray-700'}`}>{r.total_score || 0}</span>
                              </td>
                              <td className="px-3 py-2.5">
                                <span className={`badge ${RESP_STATUS_COLORS[r.status] || 'badge-gray'}`}>{r.status}</span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="text-center py-6 text-warmgray-400 text-sm">No responses yet</div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="card text-center py-12 text-warmgray-400">
          <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p>No RFQs found</p>
        </div>
      )}
    </div>
  )
}

function CreateRFQForm({ onClose, onCreated }) {
  const [form, setForm] = useState({
    title: '', category: '', department: '', budget_estimate: '', submission_deadline: '', created_by: '',
  })
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await api.post('/sourcing/rfqs', { ...form, budget_estimate: parseFloat(form.budget_estimate) || 0 })
      onCreated()
      onClose()
    } catch {
      alert('Failed to create RFQ')
    } finally {
      setSubmitting(false)
    }
  }

  const inputCls = "w-full px-3 py-2 text-sm border border-warmgray-200 rounded-lg bg-white text-warmgray-800 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"

  return (
    <div className="card mb-6 border-brand-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-warmgray-800">New RFQ</h3>
        <button onClick={onClose} className="text-warmgray-400 hover:text-warmgray-600"><X className="w-4 h-4" /></button>
      </div>
      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div className="md:col-span-2 lg:col-span-3">
          <label className="block text-xs font-medium text-warmgray-600 mb-1">Title *</label>
          <input value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} className={inputCls} required />
        </div>
        <div>
          <label className="block text-xs font-medium text-warmgray-600 mb-1">Category</label>
          <input value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} className={inputCls} placeholder="e.g. IT Services" />
        </div>
        <div>
          <label className="block text-xs font-medium text-warmgray-600 mb-1">Department</label>
          <input value={form.department} onChange={e => setForm({ ...form, department: e.target.value })} className={inputCls} />
        </div>
        <div>
          <label className="block text-xs font-medium text-warmgray-600 mb-1">Budget Estimate (INR)</label>
          <input type="number" value={form.budget_estimate} onChange={e => setForm({ ...form, budget_estimate: e.target.value })} className={inputCls} />
        </div>
        <div>
          <label className="block text-xs font-medium text-warmgray-600 mb-1">Submission Deadline</label>
          <input type="date" value={form.submission_deadline} onChange={e => setForm({ ...form, submission_deadline: e.target.value })} className={inputCls} />
        </div>
        <div>
          <label className="block text-xs font-medium text-warmgray-600 mb-1">Created By</label>
          <input value={form.created_by} onChange={e => setForm({ ...form, created_by: e.target.value })} className={inputCls} />
        </div>
        <div className="md:col-span-2 lg:col-span-3 flex justify-end gap-2">
          <button type="button" onClick={onClose} className="btn-secondary px-4 py-2 rounded-lg text-sm font-medium">Cancel</button>
          <button type="submit" disabled={submitting} className="btn-primary px-4 py-2 rounded-lg text-sm font-medium">
            {submitting ? 'Creating...' : 'Create RFQ'}
          </button>
        </div>
      </form>
    </div>
  )
}
