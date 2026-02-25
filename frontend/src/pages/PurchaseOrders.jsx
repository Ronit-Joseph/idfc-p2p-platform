import { useEffect, useState } from 'react'
import { getPOs, getPO } from '../api'
import { ShoppingCart, CheckCircle, Clock, Package, Truck, XCircle } from 'lucide-react'

const STATUS_COLOR = {
  DRAFT:              'badge badge-gray',
  SENT:               'badge badge-blue',
  ACKNOWLEDGED:       'badge badge-purple',
  PARTIALLY_RECEIVED: 'badge badge-yellow',
  RECEIVED:           'badge badge-green',
  CLOSED:             'badge badge-gray',
}

const fmtInr = v => v >= 100000 ? `₹${(v/100000).toFixed(2)}L` : `₹${v.toLocaleString('en-IN')}`

export default function PurchaseOrders() {
  const [pos, setPOs] = useState([])
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => { getPOs().then(setPOs) }, [])

  const loadDetail = (id) => {
    if (detail?.id === id) { setDetail(null); return }
    setLoading(true)
    getPO(id).then(d => { setDetail(d); setLoading(false) })
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold text-gray-900">Purchase Orders</h1>
        <p className="text-sm text-gray-500 mt-0.5">Replaces Oracle EBS Purchasing module · EBS used only for GL encumbrance posting</p>
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              {['PO #','PR Ref','Supplier','Amount','Status','GRN','EBS Commitment','Delivery Date'].map(h => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {pos.map(po => (
              <tr key={po.id} className="table-row-hover" onClick={() => loadDetail(po.id)}>
                <td className="px-4 py-3 font-mono text-xs text-blue-600 font-medium">{po.po_number}</td>
                <td className="px-4 py-3 text-xs text-gray-500 font-mono">{po.pr_id || '—'}</td>
                <td className="px-4 py-3">
                  <div className="font-medium text-gray-800 text-xs">{po.supplier_name}</div>
                </td>
                <td className="px-4 py-3 font-medium">{fmtInr(po.amount)}</td>
                <td className="px-4 py-3">
                  <span className={STATUS_COLOR[po.status] || 'badge badge-gray'}>
                    {po.status.replace(/_/g,' ')}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {po.grn_id
                    ? <span className="text-xs font-mono text-green-700 bg-green-50 px-2 py-0.5 rounded">{po.grn_id}</span>
                    : <span className="text-gray-300 text-xs">—</span>}
                </td>
                <td className="px-4 py-3">
                  <span className={`badge ${po.ebs_commitment_status === 'POSTED' ? 'badge-green' : 'badge-yellow'}`}>
                    {po.ebs_commitment_status === 'POSTED' ? '✓ GL Posted' : '⏳ Pending'}
                  </span>
                  {po.ebs_commitment_ref && <div className="text-xs font-mono text-gray-400 mt-0.5">{po.ebs_commitment_ref}</div>}
                </td>
                <td className="px-4 py-3 text-xs text-gray-500">{po.delivery_date || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Detail Panel */}
      {loading && <div className="text-center text-gray-400 py-4">Loading…</div>}
      {detail && !loading && (
        <div className="card border-blue-200 space-y-5">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="font-bold text-gray-900">{detail.po_number}</h2>
              <p className="text-sm text-gray-500">Supplier: {detail.supplier_name}</p>
            </div>
            <span className={STATUS_COLOR[detail.status] || 'badge badge-gray'}>{detail.status.replace(/_/g,' ')}</span>
          </div>

          <div className="grid grid-cols-4 gap-4 text-sm">
            <div><span className="text-xs text-gray-400">Total Amount</span><br /><span className="font-bold text-lg">{fmtInr(detail.amount)}</span></div>
            <div><span className="text-xs text-gray-400">PR Reference</span><br /><span className="font-mono text-blue-600 text-xs">{detail.pr_id || '—'}</span></div>
            <div><span className="text-xs text-gray-400">Delivery Date</span><br /><span>{detail.delivery_date || '—'}</span></div>
            <div><span className="text-xs text-gray-400">GRN</span><br /><span className="font-mono text-xs text-green-700">{detail.grn_id || 'Pending'}</span></div>
          </div>

          {/* EBS Commitment Box */}
          <div className={`rounded-lg p-4 border ${detail.ebs_commitment_status === 'POSTED' ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'}`}>
            <div className="text-xs font-semibold text-gray-600 uppercase mb-2">Oracle EBS Integration — GL Encumbrance</div>
            <div className="flex gap-8 text-sm">
              <div><span className="text-gray-500">Status</span><br />
                <span className={`font-medium ${detail.ebs_commitment_status === 'POSTED' ? 'text-green-700' : 'text-yellow-700'}`}>
                  {detail.ebs_commitment_status === 'POSTED' ? '✓ Posted to GL' : '⏳ Pending'}
                </span>
              </div>
              {detail.ebs_commitment_ref && <div><span className="text-gray-500">EBS Reference</span><br /><span className="font-mono text-xs">{detail.ebs_commitment_ref}</span></div>}
              <div><span className="text-gray-500">Module</span><br /><span className="text-xs">Oracle GL (Encumbrance)</span></div>
              <div><span className="text-gray-500">Amount</span><br /><span className="font-medium">{fmtInr(detail.amount)}</span></div>
            </div>
            <p className="text-xs text-gray-500 mt-2">P2P platform posts PO encumbrances to Oracle GL. Invoice approval will convert encumbrance → actual. Oracle EBS AP/PO UI no longer used.</p>
          </div>

          {/* Line items vs GRN */}
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Line Items & Receipt Status</p>
            <table className="w-full text-xs">
              <thead>
                <tr className="text-gray-400 border-b border-gray-100">
                  <th className="text-left py-1.5">Description</th>
                  <th className="text-center py-1.5">PO Qty</th>
                  <th className="text-center py-1.5">GRN Qty</th>
                  <th className="text-center py-1.5">Match</th>
                  <th className="text-right py-1.5">Total</th>
                </tr>
              </thead>
              <tbody>
                {detail.items?.map((item, i) => {
                  const match = item.grn_qty === item.qty
                  const partial = item.grn_qty > 0 && item.grn_qty < item.qty
                  return (
                    <tr key={i} className="border-t border-gray-50">
                      <td className="py-2 text-gray-700">{item.desc}</td>
                      <td className="py-2 text-center">{item.qty} {item.unit}</td>
                      <td className="py-2 text-center">{item.grn_qty ?? '—'}</td>
                      <td className="py-2 text-center">
                        {item.grn_qty == null ? <span className="text-gray-300">—</span>
                          : match ? <span className="text-green-600">✓ Full</span>
                          : partial ? <span className="text-yellow-600">⚡ Partial</span>
                          : <span className="text-red-500">✗ Not received</span>}
                      </td>
                      <td className="py-2 text-right font-medium">{fmtInr(item.total)}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {detail.grn && (
            <div className="bg-gray-50 rounded-lg p-3 text-sm">
              <p className="text-xs font-semibold text-gray-500 uppercase mb-1">GRN Details</p>
              <div className="flex gap-6 text-xs text-gray-600">
                <div><span className="text-gray-400">GRN#</span> {detail.grn.grn_number}</div>
                <div><span className="text-gray-400">Received</span> {detail.grn.received_date}</div>
                <div><span className="text-gray-400">By</span> {detail.grn.received_by}</div>
                <div><span className="text-gray-400">Status</span> <span className={`font-medium ${detail.grn.status === 'COMPLETE' ? 'text-green-700' : 'text-yellow-700'}`}>{detail.grn.status}</span></div>
              </div>
              {detail.grn.notes && <p className="text-xs text-gray-500 mt-1.5 italic">{detail.grn.notes}</p>}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
