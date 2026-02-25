import { useEffect, useState } from 'react'
import { getSuppliers, getVendorEvents } from '../api'
import { Users, ExternalLink, Shield, AlertTriangle, CheckCircle } from 'lucide-react'

const fmtInr = v => v >= 100000 ? `₹${(v/100000).toFixed(1)}L` : `₹${v?.toLocaleString('en-IN') ?? '—'}`

const RISK_COLOR = {
  LOW:    'text-green-700 bg-green-50',
  MEDIUM: 'text-yellow-700 bg-yellow-50',
  HIGH:   'text-red-700 bg-red-50',
}
const riskLevel = (score) => score < 2.5 ? 'LOW' : score < 3.5 ? 'MEDIUM' : 'HIGH'

const PORTAL_STATUS = {
  VERIFIED:             'badge badge-green',
  PENDING_VERIFICATION: 'badge badge-yellow',
  SUSPENDED:            'badge badge-red',
}

const VENDOR_EVENT_ICON = {
  'vendor.onboarded':        '🆕',
  'vendor.bank_verified':    '🏦',
  'vendor.gstin_updated':    '📋',
  'vendor.suspended':        '🚫',
  'vendor.document_expired': '⚠️',
}

export default function Suppliers() {
  const [suppliers, setSuppliers] = useState([])
  const [events, setEvents] = useState([])
  const [selected, setSelected] = useState(null)
  const [filter, setFilter] = useState('ALL')

  useEffect(() => {
    getSuppliers().then(setSuppliers)
    getVendorEvents().then(setEvents)
  }, [])

  const filtered = filter === 'ALL' ? suppliers
    : filter === 'MSME' ? suppliers.filter(s => s.is_msme)
    : filter === 'HIGH_RISK' ? suppliers.filter(s => s.risk_score >= 3.5)
    : suppliers

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold text-gray-900">Supplier Registry</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Vendor Portal is the system of record · P2P Supplier Service maintains a read-optimised projection via Kafka events
        </p>
      </div>

      {/* Architecture callout */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm">
        <div className="font-semibold text-blue-900 mb-2">🔗 Vendor Portal Integration</div>
        <div className="flex items-center gap-2 text-xs text-blue-800 flex-wrap">
          <span className="bg-blue-100 px-2 py-1 rounded font-medium">Vendor Portal (System of Record)</span>
          <span>→</span>
          <span className="bg-blue-100 px-2 py-1 rounded font-medium">Kafka: vendor.onboarded / bank_verified / gstin_updated</span>
          <span>→</span>
          <span className="bg-blue-100 px-2 py-1 rounded font-medium">P2P Supplier Service (projection)</span>
          <span>→</span>
          <span className="bg-blue-100 px-2 py-1 rounded font-medium">PR/PO / Invoice / Payment Engine</span>
        </div>
        <p className="text-xs text-blue-700 mt-2">No vendor can receive a payment without portal-verified bank details. Vendor suspension instantly blocks new POs and flags open invoices.</p>
      </div>

      <div className="grid grid-cols-2 gap-5">
        {/* Supplier list */}
        <div className="space-y-4">
          <div className="flex gap-2">
            {[['ALL','All'], ['MSME','MSME Only'], ['HIGH_RISK','High Risk']].map(([v, l]) => (
              <button key={v}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${filter === v ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'}`}
                onClick={() => setFilter(v)}>{l} ({v === 'ALL' ? suppliers.length : v === 'MSME' ? suppliers.filter(s => s.is_msme).length : suppliers.filter(s => s.risk_score >= 3.5).length})
              </button>
            ))}
          </div>

          <div className="card p-0 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  {['Supplier','Category','MSME','Risk','Portal',''].map(h => (
                    <th key={h} className="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {filtered.map(s => (
                  <tr key={s.id}
                    className={`table-row-hover ${selected?.id === s.id ? 'bg-blue-50' : ''}`}
                    onClick={() => setSelected(selected?.id === s.id ? null : s)}>
                    <td className="px-3 py-2.5">
                      <div className="font-medium text-gray-800 text-xs">{s.legal_name}</div>
                      <div className="font-mono text-[10px] text-gray-400">{s.gstin}</div>
                    </td>
                    <td className="px-3 py-2.5 text-xs text-gray-500">{s.category}</td>
                    <td className="px-3 py-2.5">
                      {s.is_msme
                        ? <span className="badge badge-orange text-[10px]">{s.msme_category}</span>
                        : <span className="text-gray-300 text-xs">—</span>}
                    </td>
                    <td className="px-3 py-2.5">
                      <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${RISK_COLOR[riskLevel(s.risk_score)]}`}>
                        {s.risk_score.toFixed(1)} · {riskLevel(s.risk_score)}
                      </span>
                    </td>
                    <td className="px-3 py-2.5">
                      <span className={`${PORTAL_STATUS[s.vendor_portal_status] || 'badge badge-gray'} text-[10px]`}>
                        {s.vendor_portal_status === 'VERIFIED' ? '✓ Verified' :
                         s.vendor_portal_status === 'PENDING_VERIFICATION' ? '⏳ Pending' : s.vendor_portal_status}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 text-blue-400 text-xs">›</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right column: detail + events */}
        <div className="space-y-4">
          {selected ? (
            <div className="card border-blue-200 space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-bold text-gray-900">{selected.legal_name}</h3>
                  <p className="text-xs text-gray-500 font-mono mt-0.5">{selected.gstin}</p>
                </div>
                <div className="flex gap-2">
                  {selected.is_msme && <span className="badge badge-orange">{selected.msme_category}</span>}
                  <span className={`badge ${PORTAL_STATUS[selected.vendor_portal_status] || 'badge-gray'}`}>
                    {selected.vendor_portal_status?.replace(/_/g, ' ')}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 text-sm">
                <div><span className="text-xs text-gray-400">PAN</span><br /><span className="font-mono">{selected.pan}</span></div>
                <div><span className="text-xs text-gray-400">State</span><br />{selected.state}</div>
                <div><span className="text-xs text-gray-400">Category</span><br />{selected.category}</div>
                <div><span className="text-xs text-gray-400">Payment Terms</span><br />{selected.payment_terms} days</div>
                <div><span className="text-xs text-gray-400">Bank</span><br />{selected.bank_name} · <span className="font-mono">{selected.ifsc}</span></div>
                <div><span className="text-xs text-gray-400">Account</span><br /><span className="font-mono">XXXX{selected.bank_account?.slice(-4)}</span></div>
                <div><span className="text-xs text-gray-400">Onboarded</span><br />{selected.onboarded_date}</div>
                <div><span className="text-xs text-gray-400">Last Portal Sync</span><br />{new Date(selected.last_synced_from_portal).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}</div>
              </div>

              {/* Risk score */}
              <div className={`rounded-lg p-3 ${RISK_COLOR[riskLevel(selected.risk_score)]} border`}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-semibold uppercase">Supplier Risk Score</span>
                  <span className="text-2xl font-black">{selected.risk_score.toFixed(1)}</span>
                </div>
                <div className="h-2 bg-white bg-opacity-50 rounded-full overflow-hidden">
                  <div className={`h-full rounded-full ${riskLevel(selected.risk_score) === 'LOW' ? 'bg-green-500' : riskLevel(selected.risk_score) === 'MEDIUM' ? 'bg-yellow-500' : 'bg-red-500'}`}
                    style={{ width: `${(selected.risk_score / 5) * 100}%` }} />
                </div>
                <p className="text-[10px] mt-1 opacity-70">Risk Agent — composite score from transaction history, GST compliance, document status</p>
              </div>

              {/* Payment guard */}
              <div className={`rounded-lg p-3 text-xs ${selected.vendor_portal_status === 'VERIFIED' ? 'bg-green-50 border border-green-200 text-green-800' : 'bg-yellow-50 border border-yellow-200 text-yellow-800'}`}>
                {selected.vendor_portal_status === 'VERIFIED'
                  ? <><CheckCircle className="w-3.5 h-3.5 inline mr-1" /> <strong>Payment ENABLED</strong> — bank account verified via penny drop through Vendor Portal</>
                  : <><AlertTriangle className="w-3.5 h-3.5 inline mr-1" /> <strong>Payment BLOCKED</strong> — bank verification pending in Vendor Portal</>}
              </div>
            </div>
          ) : (
            <div className="card border-dashed border-gray-200 text-center text-gray-400 py-12">
              <Users className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm">Select a supplier to view details</p>
            </div>
          )}

          {/* Vendor Portal Events */}
          <div className="card">
            <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <ExternalLink className="w-4 h-4 text-blue-500" /> Vendor Portal Event Stream
            </h3>
            <div className="space-y-2">
              {events.map(e => (
                <div key={e.id} className={`flex gap-3 text-xs rounded-lg p-2.5 border ${e.processed ? 'bg-gray-50 border-gray-100' : 'bg-yellow-50 border-yellow-200'}`}>
                  <div className="text-base flex-shrink-0">{VENDOR_EVENT_ICON[e.event_type] || '📌'}</div>
                  <div className="flex-1">
                    <div className="font-medium text-gray-800">{e.supplier_name}</div>
                    <div className="text-[10px] font-mono text-blue-600">{e.event_type}</div>
                    <div className="text-gray-500 mt-0.5">{e.p2p_action}</div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <div className="text-gray-400">{new Date(e.timestamp).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}</div>
                    <span className={`badge text-[10px] mt-1 ${e.processed ? 'badge-green' : 'badge-yellow'}`}>
                      {e.processed ? '✓ Processed' : '⏳ Pending'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
