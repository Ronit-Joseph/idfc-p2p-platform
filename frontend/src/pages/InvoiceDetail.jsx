import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getInvoice, approveInvoice, rejectInvoice, processInvoice } from '../api'
import { ArrowLeft, Shield, Database, Server, Bot, AlertTriangle, CheckCircle, XCircle, Clock, Zap, RefreshCw } from 'lucide-react'

const fmtInr = v => v != null ? (v >= 100000 ? `₹${(v/100000).toFixed(2)}L` : `₹${v.toLocaleString('en-IN')}`) : '—'

const STATUS_COLOR = {
  CAPTURED: 'bg-warmgray-100 text-warmgray-700',
  EXTRACTED: 'bg-blue-100 text-blue-800',
  VALIDATED: 'bg-purple-100 text-purple-800',
  MATCHED: 'bg-indigo-100 text-indigo-800',
  PENDING_APPROVAL: 'bg-yellow-100 text-yellow-800',
  APPROVED: 'bg-green-100 text-green-800',
  REJECTED: 'bg-red-100 text-red-800',
  POSTED_TO_EBS: 'bg-green-100 text-green-800',
  PAID: 'bg-green-100 text-green-800',
}

function Section({ title, icon: Icon, iconColor = 'text-brand-500', children, className = '' }) {
  return (
    <div className={`card ${className}`}>
      <div className={`flex items-center gap-2 mb-4 pb-3 border-b border-warmgray-100`}>
        <Icon className={`w-4 h-4 ${iconColor}`} />
        <h3 className="text-sm font-semibold text-warmgray-800">{title}</h3>
      </div>
      {children}
    </div>
  )
}

function InfoRow({ label, value, mono = false, className = '' }) {
  return (
    <div className={className}>
      <div className="text-xs text-warmgray-400 mb-0.5">{label}</div>
      <div className={`text-sm font-medium text-warmgray-800 ${mono ? 'font-mono' : ''}`}>{value ?? '—'}</div>
    </div>
  )
}

export default function InvoiceDetail() {
  const { id } = useParams()
  const nav = useNavigate()
  const [inv, setInv] = useState(null)
  const [loading, setLoading] = useState(true)
  const [acting, setActing] = useState(false)

  const load = () => {
    setLoading(true)
    getInvoice(id).then(d => { setInv(d); setLoading(false) }).catch(() => setLoading(false))
  }
  useEffect(load, [id])

  const doApprove = async () => {
    setActing(true)
    await approveInvoice(id)
    load()
    setActing(false)
  }
  const doReject = async () => {
    setActing(true)
    await rejectInvoice(id)
    load()
    setActing(false)
  }
  const doProcess = async () => {
    setActing(true)
    await processInvoice(id)
    load()
    setActing(false)
  }

  if (loading) return <div className="flex items-center justify-center h-64 text-warmgray-400">Loading invoice…</div>
  if (!inv) return <div className="text-red-500">Invoice not found</div>

  const canApprove = ['MATCHED', 'PENDING_APPROVAL', 'VALIDATED'].includes(inv.status) && !inv.fraud_flag
  const canProcess = ['CAPTURED', 'EXTRACTED', 'VALIDATED', 'MATCHED'].includes(inv.status)

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-start gap-4">
        <button className="btn-secondary py-1.5" onClick={() => nav('/invoices')}>
          <ArrowLeft className="w-4 h-4" /> Back
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-warmgray-900">{inv.invoice_number}</h1>
            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${STATUS_COLOR[inv.status] || 'bg-warmgray-100'}`}>
              {inv.status?.replace(/_/g, ' ')}
            </span>
            {inv.fraud_flag && <span className="px-3 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-800">🚨 FRAUD BLOCKED</span>}
            {inv.is_msme_supplier && (
              <span className={`px-3 py-1 rounded-full text-xs font-semibold ${inv.msme_status === 'BREACHED' ? 'bg-red-100 text-red-800' : inv.msme_status === 'AT_RISK' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'}`}>
                MSME {inv.msme_category}
              </span>
            )}
          </div>
          <p className="text-sm text-warmgray-500 mt-0.5">{inv.supplier_name} · Invoice date: {inv.invoice_date}</p>
        </div>
        <div className="flex gap-2">
          {canProcess && (
            <button className="btn-secondary text-sm" onClick={doProcess} disabled={acting}>
              <Zap className="w-4 h-4" /> Advance Processing
            </button>
          )}
          {canApprove && (
            <>
              <button className="btn-success text-sm" onClick={doApprove} disabled={acting}>
                <CheckCircle className="w-4 h-4" /> Approve
              </button>
              <button className="btn-danger text-sm" onClick={doReject} disabled={acting}>
                <XCircle className="w-4 h-4" /> Reject
              </button>
            </>
          )}
        </div>
      </div>

      {/* Invoice amount summary strip */}
      <div className="bg-gradient-to-r from-brand-600 to-brand-800 rounded-xl p-5 text-white">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
          <div>
            <div className="text-brand-200 text-xs uppercase tracking-wide">Subtotal</div>
            <div className="text-xl font-bold mt-0.5">{fmtInr(inv.subtotal)}</div>
          </div>
          <div>
            <div className="text-brand-200 text-xs uppercase tracking-wide">GST ({inv.gst_rate}%)</div>
            <div className="text-xl font-bold mt-0.5">{fmtInr(inv.gst_amount)}</div>
          </div>
          <div>
            <div className="text-brand-200 text-xs uppercase tracking-wide">Gross Total</div>
            <div className="text-xl font-bold mt-0.5">{fmtInr(inv.total_amount)}</div>
          </div>
          <div>
            <div className="text-brand-200 text-xs uppercase tracking-wide">TDS ({inv.tds_rate}%)</div>
            <div className="text-xl font-bold mt-0.5 text-yellow-300">- {fmtInr(inv.tds_amount)}</div>
          </div>
        </div>
        <div className="mt-4 pt-4 border-t border-brand-500">
          <div className="text-brand-200 text-xs uppercase tracking-wide">Net Payable</div>
          <div className="text-2xl font-bold mt-0.5 text-green-300">{fmtInr(inv.net_payable)}</div>
        </div>
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-2 gap-5">
        {/* Invoice details */}
        <Section title="Invoice Details" icon={RefreshCw} iconColor="text-warmgray-400">
          <div className="grid grid-cols-2 gap-4">
            <InfoRow label="Invoice Number" value={inv.invoice_number} mono />
            <InfoRow label="Invoice Date" value={inv.invoice_date} />
            <InfoRow label="Due Date" value={inv.due_date} />
            <InfoRow label="HSN / SAC" value={inv.hsn_sac} mono />
            <InfoRow label="Supplier GSTIN" value={inv.gstin_supplier} mono />
            <InfoRow label="Buyer GSTIN" value={inv.gstin_buyer} mono />
            <InfoRow label="PO Reference" value={inv.po_id} mono />
            <InfoRow label="GRN Reference" value={inv.grn_id} mono />
            {inv.ocr_confidence && <InfoRow label="OCR Confidence" value={`${inv.ocr_confidence}%`} />}
            {inv.irn && <InfoRow className="col-span-2" label="IRN (e-Invoice)" value={inv.irn?.slice(0,40) + '…'} mono />}
          </div>
          {inv.rejected_by && (
            <div className="mt-3 bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
              <span className="font-medium">Rejected by:</span> {inv.rejected_by}<br />
              {inv.rejection_reason && <><span className="font-medium">Reason:</span> {inv.rejection_reason}</>}
            </div>
          )}
        </Section>

        {/* GST Cache Validation */}
        <Section title="GST Validation — Cygnet Cache" icon={Database} iconColor="text-brand-500">
          {inv.gstin_validated_from_cache ? (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <div className="font-semibold text-green-800 text-sm">GSTIN Validated — From Local Cache</div>
                  <div className="text-xs text-warmgray-500">
                    Last Cygnet sync: {inv.gstin_cache_age_hours?.toFixed(1)}h ago · No live API call made
                  </div>
                </div>
              </div>
              {inv.gst_cache_data && (
                <div className="bg-warmgray-50 rounded-lg p-3 space-y-2 text-sm">
                  <div className="grid grid-cols-2 gap-3">
                    <div><span className="text-xs text-warmgray-400">Registration Type</span><br />{inv.gst_cache_data.registration_type}</div>
                    <div><span className="text-xs text-warmgray-400">Status</span><br />
                      <span className="text-green-700 font-medium">✓ {inv.gst_cache_data.status}</span></div>
                    <div><span className="text-xs text-warmgray-400">GSTR-1 Compliance</span><br />
                      <span className={inv.gst_cache_data.gstr1_compliance === 'FILED' ? 'text-green-700' : 'text-yellow-600'}>
                        {inv.gst_cache_data.gstr1_compliance}
                      </span>
                    </div>
                    <div><span className="text-xs text-warmgray-400">GSTR-2B Available</span><br />
                      {inv.gst_cache_data.gstr2b_available
                        ? <span className="text-green-700">✓ {inv.gst_cache_data.gstr2b_period}</span>
                        : <span className="text-red-500">✗ Not available</span>}
                    </div>
                  </div>
                  <div className={`mt-2 rounded px-3 py-2 text-xs font-medium ${inv.gstr2b_itc_eligible ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-700'}`}>
                    {inv.gstr2b_itc_eligible ? '✓ ITC Eligible — Input Tax Credit can be claimed' : '✗ ITC NOT Eligible — Composition dealer or GSTR-2B not filed'}
                  </div>
                </div>
              )}
              <div className="mt-3 flex items-center gap-2 text-xs text-warmgray-400">
                <Database className="w-3 h-3" />
                <span>Sync provider: <strong>Cygnet GSP</strong> · Batch mode · {inv.gst_cache_data?.cache_hit_count} cache hits to date for this GSTIN</span>
              </div>
            </div>
          ) : (
            <div className="text-center text-warmgray-400 py-6">
              <Database className="w-8 h-8 mx-auto mb-2 opacity-30" />
              <p className="text-sm">GST validation pending — invoice not yet processed</p>
            </div>
          )}
        </Section>

        {/* 3-Way Match */}
        <Section title="3-Way Matching Engine" icon={CheckCircle} iconColor={
          inv.match_status === '3WAY_MATCH_PASSED' ? 'text-green-500' :
          inv.match_status === '3WAY_MATCH_EXCEPTION' ? 'text-yellow-500' :
          inv.match_status === 'BLOCKED_FRAUD' ? 'text-red-500' : 'text-warmgray-400'
        }>
          {inv.match_status && inv.match_status !== 'PENDING' ? (
            <div>
              <div className={`rounded-lg p-3 mb-4 text-sm font-medium ${
                inv.match_status === '3WAY_MATCH_PASSED' ? 'bg-green-50 text-green-800 border border-green-200' :
                inv.match_status === '2WAY_MATCH_PASSED' ? 'bg-blue-50 text-blue-800 border border-blue-200' :
                inv.match_status === '3WAY_MATCH_EXCEPTION' ? 'bg-yellow-50 text-yellow-800 border border-yellow-200' :
                inv.match_status === 'BLOCKED_FRAUD' ? 'bg-red-50 text-red-800 border border-red-200' :
                'bg-warmgray-50 text-warmgray-700 border border-warmgray-200'
              }`}>
                {inv.match_status === '3WAY_MATCH_PASSED' && '✓ 3-Way Match PASSED — PO = GRN = Invoice'}
                {inv.match_status === '2WAY_MATCH_PASSED' && '✓ 2-Way Match PASSED — PO = Invoice (No GRN required)'}
                {inv.match_status === '3WAY_MATCH_EXCEPTION' && `⚡ Match Exception — ${inv.match_variance}% variance`}
                {inv.match_status === 'BLOCKED_FRAUD' && '🚫 BLOCKED — Fraud Detection Agent'}
                {inv.match_note && <p className="text-xs mt-1 font-normal opacity-80">{inv.match_note}</p>}
                {inv.match_exception_reason && <p className="text-xs mt-1 font-normal opacity-80">{inv.match_exception_reason}</p>}
              </div>

              {inv.purchase_order && (
                <div>
                  <p className="text-xs font-semibold text-warmgray-400 uppercase mb-2">PO vs GRN vs Invoice</p>
                  <div className="table-wrapper">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="text-warmgray-400 border-b border-warmgray-100">
                          <th className="text-left py-1.5">Item</th>
                          <th className="text-center py-1.5 text-brand-600">PO Qty</th>
                          <th className="text-center py-1.5 text-purple-600">GRN Qty</th>
                          <th className="text-center py-1.5 text-green-600">Inv Qty</th>
                          <th className="text-center py-1.5">Match</th>
                        </tr>
                      </thead>
                      <tbody>
                        {inv.purchase_order.items?.map((item, i) => {
                          const grnItem = inv.grn?.items?.find(g => g.desc === item.desc)
                          const invQty = item.grn_qty ?? item.qty
                          const grnQty = grnItem?.received_qty ?? item.grn_qty
                          const match3 = item.qty === grnQty && item.qty === invQty
                          const match2 = !grnQty ? item.qty === invQty : false
                          return (
                            <tr key={i} className="border-t border-warmgray-50">
                              <td className="py-1.5 text-warmgray-700 truncate max-w-[100px]">{item.desc}</td>
                              <td className="py-1.5 text-center text-brand-700">{item.qty}</td>
                              <td className="py-1.5 text-center text-purple-700">{grnQty ?? '—'}</td>
                              <td className="py-1.5 text-center text-green-700">{invQty}</td>
                              <td className="py-1.5 text-center">
                                {match3 ? <span className="text-green-600">✓</span>
                                 : grnQty === 0 ? <span className="text-warmgray-300">—</span>
                                 : <span className="text-yellow-600">⚡</span>}
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center text-warmgray-300 py-6 text-sm">Matching not yet run</div>
          )}
        </Section>

        {/* AI Agents */}
        <Section title="AI Agent Insights" icon={Bot} iconColor="text-purple-500">
          {inv.ai_insights?.length > 0 ? (
            <div className="space-y-3">
              {inv.ai_insights.map(ai => (
                <div key={ai.id} className={`rounded-lg p-3 border text-sm ${
                  ai.type === 'FRAUD_ALERT' ? 'bg-red-50 border-red-200' :
                  ai.type === 'MSME_SLA_RISK' || ai.type === 'MSME_SLA_BREACH' ? 'bg-yellow-50 border-yellow-200' :
                  ai.type === 'GL_CODING' ? 'bg-purple-50 border-purple-200' :
                  'bg-brand-50 border-brand-200'
                }`}>
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-bold text-warmgray-500 uppercase">{ai.agent}</span>
                        <span className={`badge text-[11px] ${ai.type === 'FRAUD_ALERT' ? 'badge-red' : ai.type.includes('MSME') ? 'badge-yellow' : 'badge-purple'}`}>
                          {ai.type.replace(/_/g,' ')}
                        </span>
                        <span className={`badge text-[11px] ${ai.applied ? 'badge-green' : 'badge-gray'}`}>
                          {ai.status}
                        </span>
                      </div>
                      <p className="font-medium text-warmgray-800">{ai.recommendation}</p>
                      <p className="text-xs text-warmgray-500 mt-1">{ai.reasoning}</p>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <div className="text-lg font-bold text-warmgray-700">{ai.confidence.toFixed(0)}%</div>
                      <div className="text-xs text-warmgray-400">confidence</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center text-warmgray-300 py-6 text-sm">AI evaluation pending</div>
          )}
        </Section>

        {/* Oracle EBS */}
        <Section title="Oracle EBS Integration" icon={Server} iconColor="text-orange-500">
          <div className="space-y-3">
            <div className="bg-brand-50 rounded-lg p-3 text-xs text-brand-700 border border-brand-200">
              <strong>P2P Platform scope:</strong> This invoice is processed here end-to-end.<br />
              Upon approval, the platform posts to Oracle AP via on-prem EBS REST adapter. Oracle EBS no longer handles invoice capture, coding, matching or approval.
            </div>
            {inv.ebs_events?.length > 0 ? (
              <div className="space-y-2">
                {inv.ebs_events.map(e => (
                  <div key={e.id} className={`rounded-lg p-3 border text-sm ${
                    e.status === 'ACKNOWLEDGED' ? 'bg-green-50 border-green-200' :
                    e.status === 'FAILED' ? 'bg-red-50 border-red-200' :
                    'bg-yellow-50 border-yellow-200'}`}>
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="font-medium text-warmgray-800">{e.description}</div>
                        <div className="text-xs text-warmgray-500 mt-0.5">Module: <strong>{e.ebs_module}</strong> · Amount: {fmtInr(e.amount)}</div>
                        {e.ebs_ref && <div className="text-xs font-mono text-warmgray-600 mt-0.5">EBS Ref: {e.ebs_ref}</div>}
                        {e.error_message && <div className="text-xs text-red-600 mt-1">{e.error_message}</div>}
                      </div>
                      <span className={`badge text-[11px] ${e.status === 'ACKNOWLEDGED' ? 'badge-green' : e.status === 'FAILED' ? 'badge-red' : 'badge-yellow'}`}>
                        {e.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-warmgray-300 py-4 text-sm">
                {inv.status === 'CAPTURED' || inv.status === 'EXTRACTED' ? 'EBS posting will happen after invoice approval' : 'No EBS events yet'}
              </div>
            )}
            {inv.ebs_ap_status === 'POSTED' && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-sm text-green-800">
                <div className="font-medium">✓ Posted to Oracle AP</div>
                <div className="text-xs mt-0.5">EBS Ref: <span className="font-mono">{inv.ebs_ap_ref}</span> · Posted: {inv.ebs_posted_at}</div>
              </div>
            )}
          </div>
        </Section>

        {/* MSME Compliance */}
        {inv.is_msme_supplier && (
          <Section title="MSME Compliance — Section 43B(h)" icon={AlertTriangle}
            iconColor={inv.msme_status === 'BREACHED' ? 'text-red-500' : inv.msme_status === 'AT_RISK' ? 'text-yellow-500' : 'text-green-500'}
            className={inv.msme_status === 'BREACHED' ? 'border-red-200' : inv.msme_status === 'AT_RISK' ? 'border-yellow-200' : ''}>
            <div className={`rounded-xl p-4 text-center mb-4 ${
              inv.msme_status === 'BREACHED' ? 'bg-red-50 border-2 border-red-300' :
              inv.msme_status === 'AT_RISK'  ? 'bg-yellow-50 border-2 border-yellow-300' :
              'bg-green-50 border-2 border-green-300'}`}>
              <div className={`text-4xl font-black ${
                inv.msme_status === 'BREACHED' ? 'text-red-600' :
                inv.msme_status === 'AT_RISK' ? 'text-yellow-600' : 'text-green-600'}`}>
                {inv.msme_days_remaining > 0 ? inv.msme_days_remaining : Math.abs(inv.msme_days_remaining)}
              </div>
              <div className="text-sm font-medium text-warmgray-700 mt-1">
                {inv.msme_status === 'BREACHED' ? `days OVERDUE — penalty accruing` :
                 inv.msme_status === 'AT_RISK' ? `days remaining to pay` : `days remaining`}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <InfoRow label="Supplier Category" value={`MSME — ${inv.msme_category}`} />
              <InfoRow label="MSME Due Date" value={inv.msme_due_date} />
              <InfoRow label="Invoice Date" value={inv.invoice_date} />
              <InfoRow label="Status" value={
                <span className={`font-semibold ${inv.msme_status === 'BREACHED' ? 'text-red-600' : inv.msme_status === 'AT_RISK' ? 'text-yellow-600' : 'text-green-600'}`}>
                  {inv.msme_status}
                </span>
              } />
              {inv.msme_penalty_amount && (
                <InfoRow className="col-span-2" label="Sec 43B(h) Penalty Accrued" value={
                  <span className="text-red-600 font-bold">{fmtInr(inv.msme_penalty_amount)}</span>
                } />
              )}
            </div>
            <div className="mt-3 text-xs text-warmgray-500 bg-warmgray-50 rounded p-2">
              Finance Act 2023, Section 43B(h): Payments to MSME suppliers must be made within 45 days (or 15 days if no written agreement). Late payment attracts compound interest @ 3× RBI rate (currently {3 * 6.5}% p.a.).
            </div>
          </Section>
        )}

        {/* Cash Optimization */}
        {inv.cash_opt_suggestion && (
          <Section title="Cash Optimization — AI Agent" icon={Bot} iconColor="text-green-500">
            <div className={`rounded-lg p-4 text-sm border ${
              inv.cash_opt_suggestion.includes('CRITICAL') || inv.cash_opt_suggestion.includes('BREACH') ? 'bg-red-50 border-red-200 text-red-800' :
              inv.cash_opt_suggestion.includes('MSME') ? 'bg-yellow-50 border-yellow-200 text-yellow-800' :
              'bg-green-50 border-green-200 text-green-800'}`}>
              {inv.cash_opt_suggestion}
            </div>
          </Section>
        )}
      </div>
    </div>
  )
}
