import { useEffect, useState } from 'react'
import { getEBSEvents, retryEBSEvent } from '../api'
import { Server, RefreshCw, CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react'

const fmtInr = v => v >= 100000 ? `₹${(v/100000).toFixed(2)}L` : `₹${v?.toLocaleString('en-IN') ?? '—'}`

const EVENT_TYPE_BADGE = {
  PO_COMMITMENT:  'bg-blue-100 text-blue-800',
  INVOICE_POST:   'bg-purple-100 text-purple-800',
  GL_JOURNAL:     'bg-gray-100 text-gray-700',
  FA_ADDITION:    'bg-orange-100 text-orange-800',
}

export default function EBSIntegration() {
  const [data, setData] = useState(null)
  const [retrying, setRetrying] = useState(null)
  const load = () => getEBSEvents().then(setData)
  useEffect(() => { load() }, [])

  const doRetry = async (id) => {
    setRetrying(id)
    await retryEBSEvent(id)
    await load()
    setRetrying(null)
  }

  if (!data) return <div className="text-gray-400 py-8 text-center">Loading…</div>

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold text-gray-900">Oracle EBS Integration</h1>
        <p className="text-sm text-gray-500 mt-0.5">P2P Platform → Oracle Integration Cloud (OIC) → EBS ISG</p>
      </div>

      {/* Scope callout */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-sm">
          <div className="font-bold text-green-900 mb-2">✓ EBS Modules RETAINED (Integration Only)</div>
          <div className="space-y-1 text-green-800 text-xs">
            <div className="flex items-center gap-2"><CheckCircle className="w-3.5 h-3.5" /> <strong>AP (Accounts Payable)</strong> — receives invoice postings, payment runs</div>
            <div className="flex items-center gap-2"><CheckCircle className="w-3.5 h-3.5" /> <strong>GL (General Ledger)</strong> — receives encumbrances, journals, accruals</div>
            <div className="flex items-center gap-2"><CheckCircle className="w-3.5 h-3.5" /> <strong>AR (Accounts Receivable)</strong> — credit notes, advance adjustments</div>
            <div className="flex items-center gap-2"><CheckCircle className="w-3.5 h-3.5" /> <strong>Fixed Assets (FA)</strong> — capex PO asset additions</div>
          </div>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm">
          <div className="font-bold text-red-900 mb-2">✗ EBS Modules DECOMMISSIONED (Replaced by P2P)</div>
          <div className="space-y-1 text-red-800 text-xs">
            <div className="flex items-center gap-2"><XCircle className="w-3.5 h-3.5" /> <strong>iProcurement (PR)</strong> → P2P Purchase Request Service</div>
            <div className="flex items-center gap-2"><XCircle className="w-3.5 h-3.5" /> <strong>Oracle Purchasing (PO)</strong> → P2P Purchase Order Service</div>
            <div className="flex items-center gap-2"><XCircle className="w-3.5 h-3.5" /> <strong>Invoice Approval UI</strong> → P2P Invoice Management Service</div>
            <div className="flex items-center gap-2"><XCircle className="w-3.5 h-3.5" /> <strong>Oracle Matching</strong> → P2P Matching Engine (3-Way)</div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Total Events', value: data.summary.total, color: 'blue' },
          { label: 'Acknowledged', value: data.summary.acknowledged, color: 'green' },
          { label: 'Pending', value: data.summary.pending, color: 'yellow' },
          { label: 'Failed', value: data.summary.failed, color: data.summary.failed > 0 ? 'red' : 'green' },
        ].map(s => (
          <div key={s.label} className={`rounded-xl border p-4 text-center ${s.color === 'red' ? 'bg-red-50 border-red-200' : s.color === 'green' ? 'bg-green-50 border-green-200' : s.color === 'yellow' ? 'bg-yellow-50 border-yellow-200' : 'bg-blue-50 border-blue-200'}`}>
            <div className={`text-2xl font-bold ${s.color === 'red' ? 'text-red-700' : s.color === 'green' ? 'text-green-700' : s.color === 'yellow' ? 'text-yellow-700' : 'text-blue-700'}`}>{s.value}</div>
            <div className="text-xs text-gray-500 mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Integration architecture */}
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 text-xs text-gray-600">
        <div className="font-semibold text-gray-700 mb-2 text-sm">Integration Flow</div>
        <div className="flex items-center gap-2 flex-wrap">
          <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded font-medium">P2P Platform Event</span>
          <span>→</span>
          <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded font-medium">Kafka Topic (ebs.outbound.*)</span>
          <span>→</span>
          <span className="bg-orange-100 text-orange-800 px-2 py-1 rounded font-medium">OIC EBS Adapter</span>
          <span>→</span>
          <span className="bg-green-100 text-green-800 px-2 py-1 rounded font-medium">EBS ISG (REST)</span>
          <span>→</span>
          <span className="bg-gray-200 text-gray-700 px-2 py-1 rounded font-medium">Oracle AP/GL/FA Open Interface</span>
        </div>
        <p className="mt-2 text-gray-500">All postings are idempotent (idempotency key on each event). Failed events auto-retry 3× with exponential backoff, then land in DLQ for manual replay.</p>
      </div>

      {/* Events table */}
      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              {['Event ID','Type','Entity','Description','EBS Module','Amount','Status','EBS Ref','Sent At',''].map(h => (
                <th key={h} className="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {data.events.map(e => (
              <tr key={e.id} className={`text-sm ${e.status === 'FAILED' ? 'bg-red-50' : ''}`}>
                <td className="px-3 py-3 font-mono text-xs text-gray-500">{e.id}</td>
                <td className="px-3 py-3">
                  <span className={`badge text-[10px] ${EVENT_TYPE_BADGE[e.event_type] || 'badge-gray'}`}>
                    {e.event_type.replace(/_/g,' ')}
                  </span>
                </td>
                <td className="px-3 py-3 font-mono text-xs text-blue-700">{e.entity_ref}</td>
                <td className="px-3 py-3 text-xs text-gray-600 max-w-[160px]">
                  <div>{e.description}</div>
                  {e.error_message && <div className="text-red-600 text-[10px] mt-0.5">{e.error_message}</div>}
                </td>
                <td className="px-3 py-3">
                  <span className="badge badge-gray text-[10px]">{e.ebs_module}</span>
                </td>
                <td className="px-3 py-3 font-medium text-xs">{fmtInr(e.amount)}</td>
                <td className="px-3 py-3">
                  <span className={`flex items-center gap-1 badge text-[10px] ${e.status === 'ACKNOWLEDGED' ? 'badge-green' : e.status === 'FAILED' ? 'badge-red' : 'badge-yellow'}`}>
                    {e.status === 'ACKNOWLEDGED' ? <><CheckCircle className="w-2.5 h-2.5" /> ACK</> :
                     e.status === 'FAILED' ? <><XCircle className="w-2.5 h-2.5" /> FAILED</> :
                     <><Clock className="w-2.5 h-2.5" /> PENDING</>}
                  </span>
                </td>
                <td className="px-3 py-3 font-mono text-xs text-gray-400">{e.ebs_ref || '—'}</td>
                <td className="px-3 py-3 text-xs text-gray-400">{e.sent_at ? new Date(e.sent_at).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '—'}</td>
                <td className="px-3 py-3">
                  {e.status === 'FAILED' && (
                    <button
                      className="btn-secondary text-xs py-1 px-2"
                      disabled={retrying === e.id}
                      onClick={() => doRetry(e.id)}>
                      <RefreshCw className={`w-3 h-3 ${retrying === e.id ? 'animate-spin' : ''}`} />
                      {retrying === e.id ? '…' : 'Retry'}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
