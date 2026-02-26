import { useEffect, useState } from 'react'
import { getApprovalMatrices, getPendingApprovals, approveStep, rejectStep } from '../api'
import { GitBranch, Clock, CheckCircle, XCircle, Shield, RefreshCw, ChevronDown, ChevronRight } from 'lucide-react'

const fmtInr = v => {
  if (!v && v !== 0) return '—'
  if (v >= 10000000) return `₹${(v/10000000).toFixed(1)}Cr`
  if (v >= 100000) return `₹${(v/100000).toFixed(1)}L`
  return `₹${v?.toLocaleString('en-IN') ?? '—'}`
}

const STATUS_BADGE = {
  PENDING:    'badge badge-yellow',
  APPROVED:   'badge badge-green',
  REJECTED:   'badge badge-red',
  ESCALATED:  'badge badge-purple',
  CANCELLED:  'badge badge-gray',
  SKIPPED:    'badge badge-gray',
}

export default function Workflow() {
  const [matrices, setMatrices] = useState([])
  const [pending, setPending] = useState([])
  const [tab, setTab] = useState('pending')
  const [expanded, setExpanded] = useState(null)
  const [loading, setLoading] = useState(true)
  const [acting, setActing] = useState(null)

  const load = () => {
    setLoading(true)
    Promise.all([getApprovalMatrices(), getPendingApprovals()])
      .then(([m, p]) => { setMatrices(m); setPending(p); setLoading(false) })
      .catch(() => setLoading(false))
  }

  useEffect(load, [])

  const handleApprove = async (instanceId) => {
    setActing(instanceId)
    try {
      await approveStep(instanceId, { approver_name: 'Priya Menon', comments: 'Approved via P2P Platform' })
      load()
    } finally {
      setActing(null)
    }
  }

  const handleReject = async (instanceId) => {
    setActing(instanceId)
    try {
      await rejectStep(instanceId, { approver_name: 'Priya Menon', comments: 'Rejected via P2P Platform' })
      load()
    } finally {
      setActing(null)
    }
  }

  if (loading) return <div className="flex items-center justify-center h-64 text-gray-400">Loading workflow…</div>

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Workflow & Approvals</h1>
          <p className="text-sm text-gray-500 mt-0.5">Multi-level approval engine · Configurable matrices by entity type, amount, department</p>
        </div>
        <button onClick={load} className="btn-secondary text-xs">
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </button>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-yellow-100 p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">Pending Approvals</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{pending.filter(p => p.status === 'PENDING').length}</p>
            </div>
            <div className="bg-yellow-50 p-2.5 rounded-lg"><Clock className="w-5 h-5 text-yellow-600" /></div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-green-100 p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">Approved</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{pending.filter(p => p.status === 'APPROVED').length}</p>
            </div>
            <div className="bg-green-50 p-2.5 rounded-lg"><CheckCircle className="w-5 h-5 text-green-600" /></div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-red-100 p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">Rejected</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{pending.filter(p => p.status === 'REJECTED').length}</p>
            </div>
            <div className="bg-red-50 p-2.5 rounded-lg"><XCircle className="w-5 h-5 text-red-600" /></div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-blue-100 p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">Approval Rules</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{matrices.length}</p>
            </div>
            <div className="bg-blue-50 p-2.5 rounded-lg"><GitBranch className="w-5 h-5 text-blue-600" /></div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
        {[['pending', 'Approval Instances'], ['matrices', 'Approval Matrix Rules']].map(([k, l]) => (
          <button key={k}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${tab === k ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'}`}
            onClick={() => setTab(k)}>{l}
          </button>
        ))}
      </div>

      {tab === 'pending' ? (
        <div className="space-y-3">
          {pending.length === 0 ? (
            <div className="card text-center text-gray-400 py-12">
              <CheckCircle className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm">No approval instances yet</p>
            </div>
          ) : pending.map(inst => (
            <div key={inst.id} className={`card border-l-4 ${
              inst.status === 'PENDING' ? 'border-l-yellow-400' :
              inst.status === 'APPROVED' ? 'border-l-green-400' :
              inst.status === 'REJECTED' ? 'border-l-red-400' : 'border-l-gray-300'
            }`}>
              <div className="flex items-center justify-between cursor-pointer" onClick={() => setExpanded(expanded === inst.id ? null : inst.id)}>
                <div className="flex items-center gap-4">
                  {expanded === inst.id ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm text-blue-700 font-medium">{inst.entity_type}</span>
                      <span className="text-gray-400">·</span>
                      <span className="font-mono text-sm text-gray-700">{inst.entity_id}</span>
                    </div>
                    <div className="text-xs text-gray-400 mt-0.5">
                      Level {inst.current_level} of {inst.total_levels}
                      {inst.amount && ` · ${fmtInr(inst.amount)}`}
                      {inst.department && ` · ${inst.department}`}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={STATUS_BADGE[inst.status] || 'badge badge-gray'}>{inst.status}</span>
                  {inst.status === 'PENDING' && (
                    <div className="flex gap-2">
                      <button
                        onClick={(e) => { e.stopPropagation(); handleApprove(inst.id) }}
                        disabled={acting === inst.id}
                        className="px-3 py-1.5 bg-green-600 text-white rounded-lg text-xs font-medium hover:bg-green-700 disabled:opacity-50">
                        Approve
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleReject(inst.id) }}
                        disabled={acting === inst.id}
                        className="px-3 py-1.5 bg-red-600 text-white rounded-lg text-xs font-medium hover:bg-red-700 disabled:opacity-50">
                        Reject
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {expanded === inst.id && inst.steps && (
                <div className="mt-4 pl-8 space-y-2">
                  <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Approval Steps</div>
                  {inst.steps.map((step, i) => (
                    <div key={step.id || i} className={`flex items-center gap-3 rounded-lg p-3 text-sm ${
                      step.status === 'APPROVED' ? 'bg-green-50 border border-green-100' :
                      step.status === 'REJECTED' ? 'bg-red-50 border border-red-100' :
                      step.status === 'PENDING' ? 'bg-yellow-50 border border-yellow-100' :
                      'bg-gray-50 border border-gray-100'
                    }`}>
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                        step.status === 'APPROVED' ? 'bg-green-200 text-green-800' :
                        step.status === 'REJECTED' ? 'bg-red-200 text-red-800' :
                        step.status === 'PENDING' ? 'bg-yellow-200 text-yellow-800' :
                        'bg-gray-200 text-gray-600'
                      }`}>
                        {step.level}
                      </div>
                      <div className="flex-1">
                        <span className="font-medium text-gray-700">{step.approver_role?.replace(/_/g, ' ')}</span>
                        {step.approver_name && <span className="text-xs text-gray-400 ml-2">({step.approver_name})</span>}
                      </div>
                      <span className={STATUS_BADGE[step.status] || 'badge badge-gray'} style={{fontSize: '10px'}}>{step.status}</span>
                      {step.comments && <span className="text-xs text-gray-400 italic">"{step.comments}"</span>}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                {['Entity Type', 'Min Amount', 'Max Amount', 'Department', 'Level', 'Approver Role', 'Active'].map(h => (
                  <th key={h} className="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {matrices.length === 0 ? (
                <tr><td colSpan={7} className="px-3 py-8 text-center text-gray-400 text-sm">No approval rules configured</td></tr>
              ) : matrices.map(m => (
                <tr key={m.id} className="table-row-hover">
                  <td className="px-3 py-3 font-medium text-gray-800">{m.entity_type}</td>
                  <td className="px-3 py-3">{m.min_amount != null ? fmtInr(m.min_amount) : '—'}</td>
                  <td className="px-3 py-3">{m.max_amount != null ? fmtInr(m.max_amount) : '—'}</td>
                  <td className="px-3 py-3 text-xs text-gray-600">{m.department || 'Any'}</td>
                  <td className="px-3 py-3">
                    <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-800 text-xs font-bold">
                      {m.level}
                    </span>
                  </td>
                  <td className="px-3 py-3">
                    <span className="badge badge-blue text-[10px]">{m.approver_role?.replace(/_/g, ' ')}</span>
                  </td>
                  <td className="px-3 py-3">
                    {m.is_active !== 'NO'
                      ? <span className="badge badge-green text-[10px]">Active</span>
                      : <span className="badge badge-gray text-[10px]">Inactive</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
