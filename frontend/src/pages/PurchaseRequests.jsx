import { useEffect, useState } from 'react'
import { getPRs, approvePR, rejectPR, createPR, checkBudget } from '../api'
import { Plus, CheckCircle, XCircle, AlertCircle, Clock, FileText, ChevronDown } from 'lucide-react'

const STATUS_BADGE = {
  DRAFT:            'badge badge-gray',
  PENDING_APPROVAL: 'badge badge-yellow',
  APPROVED:         'badge badge-green',
  REJECTED:         'badge badge-red',
  PO_CREATED:       'badge badge-blue',
}
const STATUS_ICON = {
  DRAFT:            <FileText className="w-3 h-3" />,
  PENDING_APPROVAL: <Clock className="w-3 h-3" />,
  APPROVED:         <CheckCircle className="w-3 h-3" />,
  REJECTED:         <XCircle className="w-3 h-3" />,
  PO_CREATED:       <CheckCircle className="w-3 h-3" />,
}

const fmtInr = v => v >= 100000 ? `₹${(v/100000).toFixed(2)}L` : `₹${v.toLocaleString('en-IN')}`

const DEPTS = [
  { code: 'TECH', name: 'Technology', gl: '6100-003', cc: 'CC-TECH-01' },
  { code: 'OPS',  name: 'Operations', gl: '6200-004', cc: 'CC-OPS-01' },
  { code: 'FIN',  name: 'Finance',    gl: '6300-005', cc: 'CC-FIN-01' },
  { code: 'MKT',  name: 'Marketing',  gl: '6400-003', cc: 'CC-MKT-01' },
  { code: 'HR',   name: 'HR',         gl: '6500-001', cc: 'CC-HR-01' },
  { code: 'ADMIN',name: 'Admin',      gl: '6600-001', cc: 'CC-ADMIN-01' },
]

export default function PurchaseRequests() {
  const [prs, setPRs] = useState([])
  const [filter, setFilter] = useState('ALL')
  const [showForm, setShowForm] = useState(false)
  const [selected, setSelected] = useState(null)
  const [budgetCheck, setBudgetCheck] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const [form, setForm] = useState({
    title: '', department: 'TECH', amount: '', category: 'IT Services',
    justification: '', requester: 'Demo User'
  })

  const load = () => getPRs().then(setPRs)
  useEffect(() => { load() }, [])

  const filtered = filter === 'ALL' ? prs : prs.filter(p => p.status === filter)

  const handleAmountChange = async (val) => {
    setForm(f => ({ ...f, amount: val }))
    if (val && form.department) {
      try {
        const d = await checkBudget(form.department, parseFloat(val))
        setBudgetCheck(d)
      } catch { setBudgetCheck(null) }
    }
  }

  const handleDeptChange = async (val) => {
    const dept = DEPTS.find(d => d.code === val)
    setForm(f => ({ ...f, department: val, gl_account: dept?.gl || '', cost_center: dept?.cc || '' }))
    if (form.amount) {
      const d = await checkBudget(val, parseFloat(form.amount))
      setBudgetCheck(d)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    const dept = DEPTS.find(d => d.code === form.department)
    try {
      await createPR({ ...form, amount: parseFloat(form.amount), gl_account: dept?.gl, cost_center: dept?.cc })
      setShowForm(false)
      setBudgetCheck(null)
      setForm({ title: '', department: 'TECH', amount: '', category: 'IT Services', justification: '', requester: 'Demo User' })
      load()
    } catch (err) {
      alert('Failed to create PR')
    } finally { setSubmitting(false) }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Purchase Requests</h1>
          <p className="text-sm text-gray-500 mt-0.5">Replaces Oracle EBS iProcurement module</p>
        </div>
        <button className="btn-primary" onClick={() => setShowForm(true)}>
          <Plus className="w-4 h-4" /> New PR
        </button>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 flex-wrap">
        {['ALL','PENDING_APPROVAL','APPROVED','REJECTED','PO_CREATED'].map(s => (
          <button key={s}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${filter === s ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'}`}
            onClick={() => setFilter(s)}>
            {s.replace(/_/g, ' ')} {s === 'ALL' ? `(${prs.length})` : `(${prs.filter(p => p.status === s).length})`}
          </button>
        ))}
      </div>

      {/* Create PR form */}
      {showForm && (
        <div className="card border-blue-200 bg-blue-50">
          <h2 className="text-sm font-semibold text-blue-900 mb-4 flex items-center gap-2">
            <Plus className="w-4 h-4" /> New Purchase Request
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <label className="block text-xs font-medium text-gray-700 mb-1">PR Title</label>
                <input className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                  placeholder="e.g. Cloud infrastructure upgrade Q4"
                  value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} required />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Department</label>
                <select className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                  value={form.department} onChange={e => handleDeptChange(e.target.value)}>
                  {DEPTS.map(d => <option key={d.code} value={d.code}>{d.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Amount (₹)</label>
                <input type="number" className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                  placeholder="500000"
                  value={form.amount} onChange={e => handleAmountChange(e.target.value)} required />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Category</label>
                <select className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                  value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value }))}>
                  {['IT Services','Consulting','Facilities Management','Office Supplies','Printing & Marketing','Others'].map(c => <option key={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Requester</label>
                <input className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                  value={form.requester} onChange={e => setForm(f => ({ ...f, requester: e.target.value }))} />
              </div>
              <div className="col-span-2">
                <label className="block text-xs font-medium text-gray-700 mb-1">Business Justification</label>
                <textarea rows={2} className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white resize-none"
                  placeholder="Explain why this purchase is needed"
                  value={form.justification} onChange={e => setForm(f => ({ ...f, justification: e.target.value }))} required />
              </div>
            </div>

            {/* Budget check result */}
            {budgetCheck && (
              <div className={`rounded-lg p-3 text-sm ${budgetCheck.status === 'APPROVED' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                <div className={`font-semibold ${budgetCheck.status === 'APPROVED' ? 'text-green-800' : 'text-red-800'}`}>
                  {budgetCheck.status === 'APPROVED' ? '✓ Budget check PASSED' : '✗ Budget check FAILED — Insufficient funds'}
                </div>
                <div className="text-gray-600 text-xs mt-1 space-y-0.5">
                  <div>Available: <span className="font-medium">{fmtInr(budgetCheck.available_amount)}</span> of <span className="font-medium">{fmtInr(budgetCheck.total_budget)}</span> ({budgetCheck.dept_name})</div>
                  <div>Utilization after approval: <span className="font-medium">{budgetCheck.utilization_after_pct}%</span></div>
                </div>
              </div>
            )}

            <div className="flex gap-3">
              <button type="submit" disabled={submitting} className="btn-primary">
                {submitting ? 'Submitting…' : 'Submit for Approval'}
              </button>
              <button type="button" className="btn-secondary" onClick={() => { setShowForm(false); setBudgetCheck(null) }}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {/* PR Table */}
      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              {['PR #','Title','Department','Amount','Status','Budget','Requester',''].map(h => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {filtered.map(pr => (
              <tr key={pr.id} className="table-row-hover" onClick={() => setSelected(selected?.id === pr.id ? null : pr)}>
                <td className="px-4 py-3 font-mono text-xs text-blue-600 font-medium">{pr.id}</td>
                <td className="px-4 py-3 max-w-[200px]">
                  <div className="font-medium text-gray-800 truncate">{pr.title}</div>
                  <div className="text-xs text-gray-400 mt-0.5">{pr.category}</div>
                </td>
                <td className="px-4 py-3 text-gray-600 text-xs">{pr.department}</td>
                <td className="px-4 py-3 font-medium text-gray-800">{fmtInr(pr.amount)}</td>
                <td className="px-4 py-3">
                  <span className={STATUS_BADGE[pr.status] || 'badge badge-gray'}>
                    {STATUS_ICON[pr.status]} <span className="ml-1">{pr.status.replace(/_/g,' ')}</span>
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`badge ${pr.budget_check === 'APPROVED' ? 'badge-green' : 'badge-red'}`}>
                    {pr.budget_check === 'APPROVED' ? '✓ OK' : '✗ Fail'}
                  </span>
                </td>
                <td className="px-4 py-3 text-xs text-gray-500">{pr.requester}</td>
                <td className="px-4 py-3">
                  {pr.status === 'PENDING_APPROVAL' && (
                    <div className="flex gap-2" onClick={e => e.stopPropagation()}>
                      <button className="btn-success text-xs py-1 px-2"
                        onClick={() => approvePR(pr.id).then(load)}>Approve</button>
                      <button className="btn-danger text-xs py-1 px-2"
                        onClick={() => rejectPR(pr.id).then(load)}>Reject</button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* PR Detail panel */}
      {selected && (
        <div className="card border-blue-200">
          <h3 className="text-sm font-semibold text-gray-800 mb-3">{selected.title}</h3>
          <div className="grid grid-cols-3 gap-4 text-sm mb-4">
            <div><span className="text-gray-500 text-xs">PR ID</span><br /><span className="font-mono">{selected.id}</span></div>
            <div><span className="text-gray-500 text-xs">Amount</span><br /><span className="font-medium">{fmtInr(selected.amount)}</span></div>
            <div><span className="text-gray-500 text-xs">GL Account</span><br /><span className="font-mono text-xs">{selected.gl_account}</span></div>
            <div><span className="text-gray-500 text-xs">Cost Centre</span><br /><span className="font-mono text-xs">{selected.cost_center}</span></div>
            {selected.po_id && <div><span className="text-gray-500 text-xs">PO Created</span><br /><span className="font-mono text-blue-600 text-xs">{selected.po_id}</span></div>}
            {selected.approver && <div><span className="text-gray-500 text-xs">Approved By</span><br /><span className="text-xs">{selected.approver}</span></div>}
          </div>
          {selected.justification && (
            <div className="bg-gray-50 rounded-lg p-3 text-sm text-gray-700">
              <span className="text-xs font-medium text-gray-500">Justification: </span>{selected.justification}
            </div>
          )}
          {selected.rejection_reason && (
            <div className="bg-red-50 rounded-lg p-3 text-sm text-red-700 mt-2">
              <span className="text-xs font-medium">Rejection reason: </span>{selected.rejection_reason}
            </div>
          )}
          {selected.items?.length > 0 && (
            <div className="mt-4">
              <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Line Items</p>
              <table className="w-full text-xs">
                <thead><tr className="text-gray-400">
                  <th className="text-left py-1">Description</th><th className="text-right py-1">Qty</th><th className="text-right py-1">Unit Price</th><th className="text-right py-1">Total</th>
                </tr></thead>
                <tbody>{selected.items.map((item, i) => (
                  <tr key={i} className="border-t border-gray-100">
                    <td className="py-1.5 text-gray-700">{item.desc}</td>
                    <td className="py-1.5 text-right">{item.qty} {item.unit}</td>
                    <td className="py-1.5 text-right">{fmtInr(item.unit_price)}</td>
                    <td className="py-1.5 text-right font-medium">{fmtInr(item.qty * item.unit_price)}</td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
