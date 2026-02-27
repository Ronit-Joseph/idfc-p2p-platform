import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getInvoices, exportCSV } from '../api'
import { Receipt, Shield, AlertTriangle, Clock, CheckCircle, XCircle, Eye, Download } from 'lucide-react'

const STATUS_COLOR = {
  CAPTURED:      'badge badge-gray',
  EXTRACTED:     'badge badge-blue',
  VALIDATED:     'badge badge-purple',
  MATCHED:       'badge badge-purple',
  PENDING_APPROVAL: 'badge badge-yellow',
  APPROVED:      'badge badge-green',
  REJECTED:      'badge badge-red',
  POSTED_TO_EBS: 'badge badge-green',
  PAID:          'badge badge-green',
}

const MATCH_COLOR = {
  '3WAY_MATCH_PASSED':    'text-green-700 bg-green-50',
  '2WAY_MATCH_PASSED':    'text-blue-700 bg-blue-50',
  '3WAY_MATCH_EXCEPTION': 'text-yellow-700 bg-yellow-50',
  'BLOCKED_FRAUD':        'text-red-700 bg-red-50',
  'PENDING':              'text-warmgray-400 bg-warmgray-50',
}

const fmtInr = v => v >= 100000 ? `₹${(v/100000).toFixed(2)}L` : `₹${v?.toLocaleString('en-IN') ?? '—'}`

export default function Invoices() {
  const [invoices, setInvoices] = useState([])
  const [filter, setFilter] = useState('ALL')
  const nav = useNavigate()

  useEffect(() => { getInvoices().then(setInvoices) }, [])

  const filtered = filter === 'ALL' ? invoices : invoices.filter(i => i.status === filter)
  const statuses = ['ALL', 'CAPTURED', 'EXTRACTED', 'VALIDATED', 'MATCHED', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'POSTED_TO_EBS']

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-warmgray-900">Invoice Management</h1>
          <p className="text-sm text-warmgray-500 mt-0.5">Replaces Oracle EBS Invoice Approval UI · Click any invoice for full detail</p>
        </div>
        <div className="flex gap-3 text-xs">
          <button onClick={() => exportCSV('invoices')} className="btn-secondary flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium"><Download className="w-3.5 h-3.5" />Export CSV</button>
          <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-red-700 font-medium">
            🚨 {invoices.filter(i => i.fraud_flag).length} Fraud Blocked
          </div>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg px-3 py-2 text-yellow-700 font-medium">
            ⚠️ {invoices.filter(i => i.msme_status === 'AT_RISK' || i.msme_status === 'BREACHED').length} MSME Risk
          </div>
        </div>
      </div>

      {/* Status filters */}
      <div className="flex gap-2 flex-wrap">
        {statuses.map(s => (
          <button key={s}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${filter === s ? 'bg-brand-500 text-white' : 'bg-white text-warmgray-600 border border-warmgray-200 hover:bg-warmgray-50'}`}
            onClick={() => setFilter(s)}>
            {s === 'ALL' ? `All (${invoices.length})` : `${s.replace(/_/g,' ')} (${invoices.filter(i => i.status === s).length})`}
          </button>
        ))}
      </div>

      {/* Invoice table */}
      <div className="card p-0 overflow-hidden">
        <div className="table-wrapper">
          <table className="w-full text-sm">
            <thead className="bg-warmgray-50 border-b border-warmgray-100">
              <tr>
                {['Invoice #','Supplier','Amount','GST / ITC','3-Way Match','AI Coding','Status','EBS','MSME',''].map(h => (
                  <th key={h} className="px-3 py-3 text-left text-xs font-semibold text-warmgray-500 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-warmgray-50">
              {filtered.map(inv => (
                <tr key={inv.id}
                  className={`table-row-hover ${inv.fraud_flag ? 'bg-red-50' : ''}`}
                  onClick={() => nav(`/invoices/${inv.id}`)}>
                  <td className="px-3 py-3">
                    <div className="font-mono text-xs text-brand-700 font-medium">{inv.invoice_number}</div>
                    <div className="text-xs text-warmgray-400 mt-0.5">{inv.invoice_date}</div>
                  </td>
                  <td className="px-3 py-3 max-w-[140px]">
                    <div className="text-xs font-medium text-warmgray-800 truncate">{inv.supplier_name}</div>
                    {inv.is_msme_supplier && <span className="badge badge-orange text-[11px]">MSME {inv.msme_category}</span>}
                  </td>
                  <td className="px-3 py-3">
                    <div className="font-medium text-sm">{fmtInr(inv.net_payable)}</div>
                    <div className="text-xs text-warmgray-400">+GST {fmtInr(inv.gst_amount)}</div>
                  </td>
                  <td className="px-3 py-3">
                    {inv.gstin_validated_from_cache ? (
                      <div>
                        <span className="badge badge-green text-[11px]">✓ Cache</span>
                        <div className="text-xs text-warmgray-400 mt-0.5">{inv.gstin_cache_age_hours?.toFixed(1)}h ago</div>
                      </div>
                    ) : inv.gstin_cache_status ? (
                      <span className="badge badge-blue text-[11px]">Checking</span>
                    ) : <span className="text-warmgray-300 text-xs">—</span>}
                    {inv.gstr2b_itc_eligible === false && <div className="text-red-500 text-[11px] mt-0.5">ITC risk</div>}
                  </td>
                  <td className="px-3 py-3">
                    {inv.match_status !== 'PENDING' && inv.match_status ? (
                      <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${MATCH_COLOR[inv.match_status] || 'text-warmgray-400 bg-warmgray-50'}`}>
                        {inv.match_status === '3WAY_MATCH_PASSED' ? '✓ 3-Way' :
                         inv.match_status === '2WAY_MATCH_PASSED' ? '✓ 2-Way' :
                         inv.match_status === '3WAY_MATCH_EXCEPTION' ? '⚡ Exception' :
                         inv.match_status === 'BLOCKED_FRAUD' ? '🚫 Blocked' : inv.match_status}
                      </span>
                    ) : <span className="text-warmgray-300 text-xs">—</span>}
                  </td>
                  <td className="px-3 py-3">
                    {inv.coding_agent_gl ? (
                      <div>
                        <div className="text-xs font-mono text-purple-700">{inv.coding_agent_gl}</div>
                        <div className="text-[11px] text-warmgray-400">{inv.coding_agent_confidence?.toFixed(0)}% conf.</div>
                      </div>
                    ) : <span className="text-warmgray-300 text-xs">—</span>}
                  </td>
                  <td className="px-3 py-3">
                    <span className={STATUS_COLOR[inv.status] || 'badge badge-gray'}>
                      {inv.status?.replace(/_/g,' ')}
                    </span>
                    {inv.fraud_flag && <div className="text-[11px] text-red-600 font-bold mt-0.5">🚨 FRAUD</div>}
                  </td>
                  <td className="px-3 py-3">
                    <span className={`badge text-[11px] ${
                      inv.ebs_ap_status === 'POSTED' ? 'badge-green' :
                      inv.ebs_ap_status === 'FAILED' ? 'badge-red' :
                      inv.ebs_ap_status === 'BLOCKED' ? 'badge-red' :
                      inv.ebs_ap_status === 'PENDING' ? 'badge-yellow' : 'badge-gray'}`}>
                      {inv.ebs_ap_status === 'POSTED' ? '✓ AP' :
                       inv.ebs_ap_status === 'FAILED' ? '✗ Failed' :
                       inv.ebs_ap_status === 'PENDING' ? '⏳ Pending' :
                       inv.ebs_ap_status === 'BLOCKED' ? '🚫 Blocked' : '—'}
                    </span>
                  </td>
                  <td className="px-3 py-3">
                    {inv.is_msme_supplier && (
                      <span className={`badge text-[11px] ${
                        inv.msme_status === 'BREACHED' ? 'badge-red' :
                        inv.msme_status === 'AT_RISK' ? 'badge-yellow' : 'badge-green'}`}>
                        {inv.msme_status === 'BREACHED' ? '🔴 Breach' :
                         inv.msme_status === 'AT_RISK' ? `⚠️ ${inv.msme_days_remaining}d` :
                         `✓ ${inv.msme_days_remaining}d`}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-3">
                    <Eye className="w-4 h-4 text-warmgray-300 hover:text-brand-500" />
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
