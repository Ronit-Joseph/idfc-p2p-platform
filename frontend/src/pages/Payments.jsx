import { useEffect, useState } from 'react'
import { getPayments, getPaymentSummary, getPaymentRuns, createPaymentRun, processPaymentRun } from '../api'
import { CreditCard, Banknote, Clock, CheckCircle, PlayCircle, RefreshCw } from 'lucide-react'

const fmtInr = v => {
  if (!v && v !== 0) return '—'
  if (v >= 10000000) return `₹${(v/10000000).toFixed(1)}Cr`
  if (v >= 100000) return `₹${(v/100000).toFixed(2)}L`
  return `₹${v?.toLocaleString('en-IN') ?? '—'}`
}

const STATUS_BADGE = {
  DRAFT:      'badge badge-gray',
  SCHEDULED:  'badge badge-blue',
  PROCESSING: 'badge badge-yellow',
  COMPLETED:  'badge badge-green',
  FAILED:     'badge badge-red',
  CANCELLED:  'badge badge-red',
}

const PAYMENT_STATUS = {
  PENDING:    'badge badge-yellow',
  COMPLETED:  'badge badge-green',
  FAILED:     'badge badge-red',
}

export default function Payments() {
  const [payments, setPayments] = useState([])
  const [runs, setRuns] = useState([])
  const [summary, setSummary] = useState(null)
  const [tab, setTab] = useState('runs')
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState(null)

  const load = () => {
    setLoading(true)
    Promise.all([getPayments(), getPaymentRuns(), getPaymentSummary()])
      .then(([p, r, s]) => { setPayments(p); setRuns(r); setSummary(s); setLoading(false) })
      .catch(() => setLoading(false))
  }

  useEffect(load, [])

  const handleProcess = async (runId) => {
    setProcessing(runId)
    try {
      await processPaymentRun(runId)
      load()
    } finally {
      setProcessing(null)
    }
  }

  if (loading) return <div className="flex items-center justify-center h-64 text-gray-400">Loading payments…</div>

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Payment Processing</h1>
          <p className="text-sm text-gray-500 mt-0.5">Bank payment runs · NEFT / RTGS / IMPS · TDS auto-deduction</p>
        </div>
        <button onClick={load} className="btn-secondary text-xs">
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </button>
      </div>

      {/* Summary cards */}
      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl border border-blue-100 p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">Total Payments</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{summary.total_payments}</p>
              </div>
              <div className="bg-blue-50 p-2.5 rounded-lg"><CreditCard className="w-5 h-5 text-blue-600" /></div>
            </div>
          </div>
          <div className="bg-white rounded-xl border border-green-100 p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">Total Disbursed</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{fmtInr(summary.total_amount)}</p>
              </div>
              <div className="bg-green-50 p-2.5 rounded-lg"><Banknote className="w-5 h-5 text-green-600" /></div>
            </div>
          </div>
          <div className="bg-white rounded-xl border border-yellow-100 p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">Pending</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{summary.pending || 0}</p>
              </div>
              <div className="bg-yellow-50 p-2.5 rounded-lg"><Clock className="w-5 h-5 text-yellow-600" /></div>
            </div>
          </div>
          <div className="bg-white rounded-xl border border-green-100 p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">Completed</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{summary.completed || 0}</p>
              </div>
              <div className="bg-green-50 p-2.5 rounded-lg"><CheckCircle className="w-5 h-5 text-green-600" /></div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2">
        {[['runs', 'Payment Runs'], ['payments', 'Individual Payments']].map(([k, l]) => (
          <button key={k}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${tab === k ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'}`}
            onClick={() => setTab(k)}>{l}
          </button>
        ))}
      </div>

      {tab === 'runs' ? (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                {['Run #', 'Method', 'Invoices', 'Total Amount', 'Status', 'Bank Ref', 'Initiated By', 'Created', ''].map(h => (
                  <th key={h} className="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {runs.length === 0 ? (
                <tr><td colSpan={9} className="px-3 py-8 text-center text-gray-400 text-sm">No payment runs yet</td></tr>
              ) : runs.map(r => (
                <tr key={r.id} className="table-row-hover">
                  <td className="px-3 py-3 font-mono text-xs text-blue-700 font-medium">{r.run_number}</td>
                  <td className="px-3 py-3"><span className="badge badge-blue text-[10px]">{r.payment_method}</span></td>
                  <td className="px-3 py-3 text-sm font-medium">{r.invoice_count}</td>
                  <td className="px-3 py-3 font-medium">{fmtInr(r.total_amount)}</td>
                  <td className="px-3 py-3"><span className={STATUS_BADGE[r.status] || 'badge badge-gray'}>{r.status}</span></td>
                  <td className="px-3 py-3 font-mono text-xs text-gray-500">{r.bank_file_ref || '—'}</td>
                  <td className="px-3 py-3 text-xs text-gray-500">{r.initiated_by || '—'}</td>
                  <td className="px-3 py-3 text-xs text-gray-400">{r.created_at ? new Date(r.created_at).toLocaleDateString('en-IN') : '—'}</td>
                  <td className="px-3 py-3">
                    {(r.status === 'DRAFT' || r.status === 'SCHEDULED' || r.status === 'PROCESSING') && (
                      <button
                        onClick={() => handleProcess(r.id)}
                        disabled={processing === r.id}
                        className="text-blue-600 hover:text-blue-800 text-xs font-medium flex items-center gap-1">
                        <PlayCircle className="w-3.5 h-3.5" />
                        {processing === r.id ? 'Processing…' : 'Advance'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                {['Payment #', 'Invoice', 'Supplier', 'Amount', 'TDS', 'Net Amount', 'Status', 'UTR', 'Date'].map(h => (
                  <th key={h} className="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {payments.length === 0 ? (
                <tr><td colSpan={9} className="px-3 py-8 text-center text-gray-400 text-sm">No payments yet</td></tr>
              ) : payments.map(p => (
                <tr key={p.id} className="table-row-hover">
                  <td className="px-3 py-3 font-mono text-xs text-blue-700 font-medium">{p.payment_number}</td>
                  <td className="px-3 py-3 font-mono text-xs">{p.invoice_number}</td>
                  <td className="px-3 py-3 text-xs text-gray-700">{p.supplier_name}</td>
                  <td className="px-3 py-3 font-medium">{fmtInr(p.amount)}</td>
                  <td className="px-3 py-3 text-red-600 text-xs">{p.tds_deducted ? `-${fmtInr(p.tds_deducted)}` : '—'}</td>
                  <td className="px-3 py-3 font-medium text-green-700">{fmtInr(p.net_amount)}</td>
                  <td className="px-3 py-3"><span className={PAYMENT_STATUS[p.status] || 'badge badge-gray'}>{p.status}</span></td>
                  <td className="px-3 py-3 font-mono text-[10px] text-gray-500">{p.bank_reference || '—'}</td>
                  <td className="px-3 py-3 text-xs text-gray-400">{p.payment_date ? new Date(p.payment_date).toLocaleDateString('en-IN') : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
