import { useState, useEffect } from 'react'
import { FileSignature, Plus, AlertTriangle, CheckCircle2, Clock, XCircle, ChevronDown, ChevronUp, X } from 'lucide-react'
import api from '../api'

const TYPE_COLORS = {
  MSA: 'badge-brand',
  SOW: 'badge-purple',
  NDA: 'badge-yellow',
  SLA: 'badge-blue',
  AMENDMENT: 'badge-orange',
}

const STATUS_COLORS = {
  DRAFT: 'badge-gray',
  ACTIVE: 'badge-green',
  EXPIRED: 'badge-red',
  TERMINATED: 'badge-red',
  RENEWED: 'badge-blue',
}

function fmt(amount) {
  if (!amount) return '—'
  if (amount >= 10000000) return `₹${(amount / 10000000).toFixed(1)}Cr`
  if (amount >= 100000) return `₹${(amount / 100000).toFixed(1)}L`
  return `₹${amount.toLocaleString('en-IN')}`
}

function daysUntil(dateStr) {
  if (!dateStr) return null
  const end = new Date(dateStr)
  const now = new Date()
  return Math.ceil((end - now) / (1000 * 60 * 60 * 24))
}

export default function Contracts() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('ALL')
  const [showForm, setShowForm] = useState(false)
  const [expandedId, setExpandedId] = useState(null)

  const load = () => {
    setLoading(true)
    api.get('/contracts').then(r => { setData(r.data); setLoading(false) }).catch(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  if (loading || !data) return (
    <div className="flex items-center justify-center py-20 text-warmgray-400">
      <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  const { contracts, summary } = data
  const filtered = filter === 'ALL' ? contracts : contracts.filter(c => c.status === filter)

  const stats = [
    { label: 'Total Contracts', value: summary.total, icon: FileSignature, color: 'text-brand-600 bg-brand-50' },
    { label: 'Active', value: summary.active, icon: CheckCircle2, color: 'text-emerald-600 bg-emerald-50' },
    { label: 'Expiring Soon', value: summary.expiring_soon, icon: AlertTriangle, color: 'text-amber-600 bg-amber-50' },
    { label: 'Expired', value: summary.expired, icon: XCircle, color: 'text-red-600 bg-red-50' },
  ]

  return (
    <div>
      <div className="page-header flex items-center justify-between">
        <div>
          <h1 className="page-title">Contract Management</h1>
          <p className="page-subtitle">Manage vendor agreements, renewals, and compliance</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium">
          <Plus className="w-4 h-4" /> New Contract
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
      {showForm && <CreateContractForm onClose={() => setShowForm(false)} onCreated={load} />}

      {/* Filters */}
      <div className="flex items-center gap-2 mb-4">
        {['ALL', 'ACTIVE', 'DRAFT', 'EXPIRED', 'TERMINATED'].map(f => (
          <button key={f} onClick={() => setFilter(f)} className={filter === f ? 'filter-pill filter-pill-active' : 'filter-pill filter-pill-inactive'}>
            {f === 'ALL' ? 'All' : f.charAt(0) + f.slice(1).toLowerCase()}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="card p-0">
        <div className="table-wrapper">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-warmgray-100">
                <th className="text-left px-5 py-3 text-xs font-medium uppercase tracking-wider text-warmgray-400">Contract</th>
                <th className="text-left px-5 py-3 text-xs font-medium uppercase tracking-wider text-warmgray-400">Supplier</th>
                <th className="text-left px-5 py-3 text-xs font-medium uppercase tracking-wider text-warmgray-400">Type</th>
                <th className="text-left px-5 py-3 text-xs font-medium uppercase tracking-wider text-warmgray-400">Status</th>
                <th className="text-left px-5 py-3 text-xs font-medium uppercase tracking-wider text-warmgray-400">Value</th>
                <th className="text-left px-5 py-3 text-xs font-medium uppercase tracking-wider text-warmgray-400">End Date</th>
                <th className="text-left px-5 py-3 text-xs font-medium uppercase tracking-wider text-warmgray-400">Expiry</th>
                <th className="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(c => {
                const days = daysUntil(c.end_date)
                const expiryClass = c.status === 'EXPIRED' || (days !== null && days < 0) ? 'text-red-600 font-medium' :
                  days !== null && days <= 30 ? 'text-amber-600 font-medium' : 'text-warmgray-500'
                const expiryText = c.status === 'EXPIRED' ? 'Expired' :
                  c.status === 'TERMINATED' ? 'Terminated' :
                  days === null ? '—' :
                  days < 0 ? `${Math.abs(days)}d overdue` :
                  `${days}d remaining`
                return (
                  <tr key={c.id} className="border-b border-warmgray-50 table-row-hover" onClick={() => setExpandedId(expandedId === c.id ? null : c.id)}>
                    <td className="px-5 py-3">
                      <div className="font-medium text-warmgray-800">{c.contract_number}</div>
                      <div className="text-xs text-warmgray-500 truncate max-w-[200px]">{c.title}</div>
                    </td>
                    <td className="px-5 py-3 text-warmgray-600">{c.supplier_name || '—'}</td>
                    <td className="px-5 py-3"><span className={`badge ${TYPE_COLORS[c.contract_type] || 'badge-gray'}`}>{c.contract_type}</span></td>
                    <td className="px-5 py-3"><span className={`badge ${STATUS_COLORS[c.status] || 'badge-gray'}`}>{c.status}</span></td>
                    <td className="px-5 py-3 font-medium text-warmgray-800">{fmt(c.value)}</td>
                    <td className="px-5 py-3 text-warmgray-500">{c.end_date || '—'}</td>
                    <td className={`px-5 py-3 text-xs ${expiryClass}`}>{expiryText}</td>
                    <td className="px-5 py-3">
                      {expandedId === c.id ? <ChevronUp className="w-4 h-4 text-warmgray-400" /> : <ChevronDown className="w-4 h-4 text-warmgray-400" />}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 && (
          <div className="text-center py-12 text-warmgray-400">
            <FileSignature className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No contracts found</p>
          </div>
        )}
      </div>
    </div>
  )
}

function CreateContractForm({ onClose, onCreated }) {
  const [form, setForm] = useState({
    title: '', supplier_name: '', contract_type: 'MSA',
    start_date: '', end_date: '', value: '', department: '', owner: '', terms_summary: '',
  })
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await api.post('/contracts', { ...form, value: parseFloat(form.value) || 0 })
      onCreated()
      onClose()
    } catch {
      alert('Failed to create contract')
    } finally {
      setSubmitting(false)
    }
  }

  const inputCls = "w-full px-3 py-2 text-sm border border-warmgray-200 rounded-lg bg-white text-warmgray-800 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"

  return (
    <div className="card mb-6 border-brand-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-warmgray-800">New Contract</h3>
        <button onClick={onClose} className="text-warmgray-400 hover:text-warmgray-600"><X className="w-4 h-4" /></button>
      </div>
      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div>
          <label className="block text-xs font-medium text-warmgray-600 mb-1">Title *</label>
          <input value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} className={inputCls} required />
        </div>
        <div>
          <label className="block text-xs font-medium text-warmgray-600 mb-1">Supplier</label>
          <input value={form.supplier_name} onChange={e => setForm({ ...form, supplier_name: e.target.value })} className={inputCls} />
        </div>
        <div>
          <label className="block text-xs font-medium text-warmgray-600 mb-1">Type</label>
          <select value={form.contract_type} onChange={e => setForm({ ...form, contract_type: e.target.value })} className={inputCls}>
            {['MSA', 'SOW', 'NDA', 'SLA', 'AMENDMENT'].map(t => <option key={t}>{t}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-warmgray-600 mb-1">Start Date</label>
          <input type="date" value={form.start_date} onChange={e => setForm({ ...form, start_date: e.target.value })} className={inputCls} />
        </div>
        <div>
          <label className="block text-xs font-medium text-warmgray-600 mb-1">End Date</label>
          <input type="date" value={form.end_date} onChange={e => setForm({ ...form, end_date: e.target.value })} className={inputCls} />
        </div>
        <div>
          <label className="block text-xs font-medium text-warmgray-600 mb-1">Value (INR)</label>
          <input type="number" value={form.value} onChange={e => setForm({ ...form, value: e.target.value })} className={inputCls} />
        </div>
        <div>
          <label className="block text-xs font-medium text-warmgray-600 mb-1">Department</label>
          <input value={form.department} onChange={e => setForm({ ...form, department: e.target.value })} className={inputCls} />
        </div>
        <div>
          <label className="block text-xs font-medium text-warmgray-600 mb-1">Owner</label>
          <input value={form.owner} onChange={e => setForm({ ...form, owner: e.target.value })} className={inputCls} />
        </div>
        <div className="md:col-span-2 lg:col-span-3">
          <label className="block text-xs font-medium text-warmgray-600 mb-1">Terms Summary</label>
          <textarea value={form.terms_summary} onChange={e => setForm({ ...form, terms_summary: e.target.value })} rows={2} className={inputCls} />
        </div>
        <div className="md:col-span-2 lg:col-span-3 flex justify-end gap-2">
          <button type="button" onClick={onClose} className="btn-secondary px-4 py-2 rounded-lg text-sm font-medium">Cancel</button>
          <button type="submit" disabled={submitting} className="btn-primary px-4 py-2 rounded-lg text-sm font-medium">
            {submitting ? 'Creating...' : 'Create Contract'}
          </button>
        </div>
      </form>
    </div>
  )
}
