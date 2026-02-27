import { useEffect, useState } from 'react'
import { getTDSDeductions, getTDSSummary, getTDSRates } from '../api'
import { Calculator, FileText, IndianRupee, RefreshCw, Info } from 'lucide-react'

const fmtInr = v => {
  if (!v && v !== 0) return '—'
  if (v >= 10000000) return `₹${(v/10000000).toFixed(1)}Cr`
  if (v >= 100000) return `₹${(v/100000).toFixed(2)}L`
  return `₹${v?.toLocaleString('en-IN') ?? '—'}`
}

const STATUS_BADGE = {
  PENDING:     'badge badge-yellow',
  DEDUCTED:    'badge badge-yellow',
  DEPOSITED:   'badge badge-blue',
  CERTIFICATE: 'badge badge-green',
}

const SECTION_COLOR = {
  '194C': 'bg-blue-100 text-blue-800',
  '194J': 'bg-purple-100 text-purple-800',
  '194H': 'bg-green-100 text-green-800',
  '194I': 'bg-yellow-100 text-yellow-800',
  '194Q': 'bg-orange-100 text-orange-800',
  '194A': 'bg-red-100 text-red-800',
}

export default function TDSManagement() {
  const [deductions, setDeductions] = useState([])
  const [summary, setSummary] = useState(null)
  const [rates, setRates] = useState(null)
  const [tab, setTab] = useState('deductions')
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    Promise.all([getTDSDeductions(), getTDSSummary(), getTDSRates()])
      .then(([d, s, r]) => { setDeductions(d); setSummary(s); setRates(r); setLoading(false) })
      .catch(() => setLoading(false))
  }

  useEffect(load, [])

  if (loading) return <div className="flex items-center justify-center h-64 text-warmgray-400">Loading TDS data…</div>

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-warmgray-900">TDS Management</h1>
          <p className="text-sm text-warmgray-500 mt-0.5">Tax Deducted at Source · Section 194C / 194J / 194H / 194I · Auto-calculation with 4% H&E Cess</p>
        </div>
        <button onClick={load} className="btn-secondary text-xs">
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </button>
      </div>

      {/* Summary cards */}
      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl border border-purple-100 p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-warmgray-500 font-medium uppercase tracking-wide">Total Deductions</p>
                <p className="text-2xl font-bold text-warmgray-900 mt-1">{summary.total_deductions}</p>
              </div>
              <div className="bg-purple-50 p-2.5 rounded-lg"><Calculator className="w-5 h-5 text-purple-600" /></div>
            </div>
          </div>
          <div className="bg-white rounded-xl border border-red-100 p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-warmgray-500 font-medium uppercase tracking-wide">Total TDS Amount</p>
                <p className="text-2xl font-bold text-warmgray-900 mt-1">{fmtInr(summary.total_tds_amount)}</p>
              </div>
              <div className="bg-red-50 p-2.5 rounded-lg"><IndianRupee className="w-5 h-5 text-red-600" /></div>
            </div>
          </div>
          <div className="bg-white rounded-xl border border-brand-100 p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-warmgray-500 font-medium uppercase tracking-wide">Deposited</p>
                <p className="text-2xl font-bold text-warmgray-900 mt-1">{summary.deposited || 0}</p>
              </div>
              <div className="bg-brand-50 p-2.5 rounded-lg"><FileText className="w-5 h-5 text-brand-600" /></div>
            </div>
          </div>
          <div className="bg-white rounded-xl border border-green-100 p-5">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-warmgray-500 font-medium uppercase tracking-wide">Form 16A Pending</p>
                <p className="text-2xl font-bold text-warmgray-900 mt-1">{summary.form16a_pending || 0}</p>
              </div>
              <div className="bg-green-50 p-2.5 rounded-lg"><FileText className="w-5 h-5 text-green-600" /></div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2">
        {[['deductions', 'Deductions'], ['rates', 'TDS Rate Card']].map(([k, l]) => (
          <button key={k}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${tab === k ? 'bg-brand-500 text-white' : 'bg-white text-warmgray-600 border border-warmgray-200 hover:bg-warmgray-50'}`}
            onClick={() => setTab(k)}>{l}
          </button>
        ))}
      </div>

      {tab === 'deductions' ? (
        <div className="card p-0 overflow-hidden">
          <div className="table-wrapper">
          <table className="w-full text-sm">
            <thead className="bg-warmgray-50 border-b border-warmgray-100">
              <tr>
                {['Invoice', 'Supplier', 'Section', 'Rate', 'Base Amount', 'TDS', 'Cess', 'Total TDS', 'Status', 'FY / Q'].map(h => (
                  <th key={h} className="px-3 py-3 text-left text-xs font-semibold text-warmgray-500 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-warmgray-50">
              {deductions.length === 0 ? (
                <tr><td colSpan={10} className="px-3 py-8 text-center text-warmgray-400 text-sm">No TDS deductions yet</td></tr>
              ) : deductions.map(d => (
                <tr key={d.id} className="table-row-hover">
                  <td className="px-3 py-3 font-mono text-xs text-brand-700 font-medium">{d.invoice_number}</td>
                  <td className="px-3 py-3 text-xs text-warmgray-700">{d.supplier_name}</td>
                  <td className="px-3 py-3">
                    <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${SECTION_COLOR[d.section] || 'bg-warmgray-100 text-warmgray-800'}`}>
                      {d.section}
                    </span>
                  </td>
                  <td className="px-3 py-3 font-medium">{d.tds_rate}%</td>
                  <td className="px-3 py-3">{fmtInr(d.base_amount)}</td>
                  <td className="px-3 py-3 text-red-600 font-medium">{fmtInr(d.tds_amount)}</td>
                  <td className="px-3 py-3 text-xs text-warmgray-500">{fmtInr(d.cess)}</td>
                  <td className="px-3 py-3 font-bold text-red-700">{fmtInr(d.total_tds)}</td>
                  <td className="px-3 py-3"><span className={STATUS_BADGE[d.status] || 'badge badge-gray'}>{d.status}</span></td>
                  <td className="px-3 py-3 text-xs text-warmgray-500">{d.fiscal_year} Q{d.quarter}</td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </div>
      ) : (
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Info className="w-4 h-4 text-blue-500" />
            <h3 className="text-sm font-semibold text-warmgray-700">TDS Rate Card — Income Tax Act Sections</h3>
          </div>
          {rates ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(rates).map(([section, info]) => (
                <div key={section} className="rounded-xl border border-warmgray-200 p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between mb-3">
                    <span className={`text-xs font-bold px-3 py-1 rounded-full ${SECTION_COLOR[section] || 'bg-warmgray-100 text-warmgray-800'}`}>
                      Section {section}
                    </span>
                  </div>
                  <p className="text-sm text-warmgray-700 font-medium mb-3">{info.description}</p>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-warmgray-500">Individual / HUF</span>
                      <span className="font-bold text-warmgray-900">{info.individual}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-warmgray-500">Company</span>
                      <span className="font-bold text-warmgray-900">{info.company}%</span>
                    </div>
                    <div className="flex justify-between border-t pt-2 mt-2">
                      <span className="text-warmgray-500">+ H&E Cess</span>
                      <span className="font-medium text-warmgray-600">4%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-warmgray-400 text-sm">Loading rates…</p>
          )}
        </div>
      )}
    </div>
  )
}
