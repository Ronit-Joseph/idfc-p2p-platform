import { useEffect, useState } from 'react'
import { getMSME } from '../api'
import { useNavigate } from 'react-router-dom'
import { AlertTriangle, Clock, CheckCircle } from 'lucide-react'

const fmtInr = v => v >= 100000 ? `₹${(v/100000).toFixed(2)}L` : `₹${v?.toLocaleString('en-IN') ?? '—'}`

export default function MSMECompliance() {
  const [data, setData] = useState(null)
  const nav = useNavigate()
  useEffect(() => { getMSME().then(setData) }, [])

  if (!data) return <div className="text-warmgray-400 py-8 text-center">Loading…</div>

  const { summary, invoices } = data

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold text-warmgray-900">MSME Compliance Dashboard</h1>
        <p className="text-sm text-warmgray-500 mt-0.5">{summary.section_43bh} · Max {summary.max_payment_days} days · Penalty: {summary.penalty_multiplier}× RBI rate ({summary.rbi_rate}%)</p>
      </div>

      {/* Policy callout */}
      <div className="bg-orange-50 border border-orange-200 rounded-xl p-4 text-sm">
        <div className="font-bold text-orange-900 mb-1">⚖️ Section 43B(h) — Finance Act 2023 (Effective Apr 1, 2024)</div>
        <div className="text-orange-800 text-xs space-y-0.5">
          <p>• Payments to MSME vendors must be made within <strong>45 days</strong> of invoice date (or 15 days if no written agreement)</p>
          <p>• Late payment attracts <strong>compound interest @ {summary.penalty_multiplier}× RBI rate ({summary.penalty_multiplier * summary.rbi_rate}% p.a.)</strong></p>
          <p>• Overdue MSME payments cannot be deducted from books for income tax purposes — <strong>direct P&L impact</strong></p>
          <p>• Vendors can file complaints at MSME SAMADHAAN portal — regulatory visibility</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card text-center">
          <div className="text-3xl font-bold text-warmgray-800">{summary.total_msme_invoices}</div>
          <div className="text-xs text-warmgray-500 mt-1">Total MSME Invoices</div>
        </div>
        <div className="card text-center bg-green-50 border-green-200">
          <div className="text-3xl font-bold text-green-700">{summary.on_track}</div>
          <div className="text-xs text-green-600 mt-1">✓ On Track</div>
        </div>
        <div className="card text-center bg-yellow-50 border-yellow-200">
          <div className="text-3xl font-bold text-yellow-700">{summary.at_risk}</div>
          <div className="text-xs text-yellow-600 mt-1">⚠️ At Risk (&lt; 10 days)</div>
        </div>
        <div className="card text-center bg-red-50 border-red-200">
          <div className="text-3xl font-bold text-red-700">{summary.breached}</div>
          <div className="text-xs text-red-600 mt-1">🔴 Breached</div>
          {summary.total_penalty_accrued > 0 && (
            <div className="text-xs text-red-500 font-bold mt-1">Penalty: {fmtInr(summary.total_penalty_accrued)}</div>
          )}
        </div>
      </div>

      {/* Invoice list */}
      <div className="card p-0 overflow-hidden">
        <div className="table-wrapper">
          <table className="w-full text-sm">
            <thead className="bg-warmgray-50 border-b border-warmgray-100">
              <tr>
                {['Invoice','Supplier','MSME Category','Invoice Date','Amount','Status','MSME Due','Days','Risk',''].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-warmgray-500 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-warmgray-50">
              {invoices.map(inv => (
                <tr key={inv.invoice_id}
                  className={`cursor-pointer transition-colors ${
                    inv.risk_level === 'RED' ? 'bg-red-50 hover:bg-red-100' :
                    inv.risk_level === 'AMBER' ? 'bg-yellow-50 hover:bg-yellow-100' :
                    'hover:bg-warmgray-50'}`}
                  onClick={() => nav(`/invoices/${inv.invoice_id}`)}>
                  <td className="px-4 py-3 font-mono text-xs text-brand-700">{inv.invoice_number}</td>
                  <td className="px-4 py-3 text-xs font-medium text-warmgray-800">{inv.supplier_name}</td>
                  <td className="px-4 py-3">
                    <span className="badge badge-orange text-[11px]">{inv.msme_category}</span>
                  </td>
                  <td className="px-4 py-3 text-xs text-warmgray-500">{inv.invoice_date}</td>
                  <td className="px-4 py-3 font-medium text-sm">{fmtInr(inv.invoice_amount)}</td>
                  <td className="px-4 py-3">
                    <span className={`badge text-[11px] ${inv.invoice_status === 'APPROVED' || inv.invoice_status === 'POSTED_TO_EBS' ? 'badge-green' : 'badge-yellow'}`}>
                      {inv.invoice_status?.replace(/_/g,' ')}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-warmgray-500">{inv.msme_due_date}</td>
                  <td className="px-4 py-3">
                    <span className={`text-lg font-black ${inv.risk_level === 'RED' ? 'text-red-600' : inv.risk_level === 'AMBER' ? 'text-yellow-600' : 'text-green-600'}`}>
                      {inv.days_remaining > 0 ? inv.days_remaining : Math.abs(inv.days_remaining)}
                    </span>
                    <span className="text-xs text-warmgray-400 ml-1">{inv.days_remaining < 0 ? 'overdue' : 'remaining'}</span>
                  </td>
                  <td className="px-4 py-3">
                    <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold ${
                      inv.risk_level === 'RED' ? 'bg-red-100 text-red-800' :
                      inv.risk_level === 'AMBER' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'}`}>
                      {inv.risk_level === 'RED' ? <><AlertTriangle className="w-3 h-3" /> BREACH</> :
                       inv.risk_level === 'AMBER' ? <><Clock className="w-3 h-3" /> AT RISK</> :
                       <><CheckCircle className="w-3 h-3" /> ON TRACK</>}
                    </div>
                    {inv.penalty_amount && (
                      <div className="text-xs text-red-600 font-bold mt-1">Penalty: {fmtInr(inv.penalty_amount)}</div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {(inv.risk_level === 'RED' || inv.risk_level === 'AMBER') && (
                      <button
                        className="btn-danger text-xs py-1 px-2"
                        onClick={e => { e.stopPropagation(); nav(`/invoices/${inv.invoice_id}`) }}>
                        Take Action
                      </button>
                    )}
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
