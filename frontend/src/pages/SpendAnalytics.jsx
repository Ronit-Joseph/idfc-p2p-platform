import { useEffect, useState } from 'react'
import { getSpendAnalytics } from '../api'
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, Legend
} from 'recharts'
import { BarChart3 } from 'lucide-react'

const fmtInr = v => v >= 10000000 ? `₹${(v/10000000).toFixed(1)}Cr` : v >= 100000 ? `₹${(v/100000).toFixed(1)}L` : `₹${v?.toLocaleString('en-IN')}`

export default function SpendAnalytics() {
  const [data, setData] = useState(null)
  useEffect(() => { getSpendAnalytics().then(setData) }, [])
  if (!data) return <div className="text-warmgray-400 py-8 text-center">Loading analytics…</div>

  const { spend_by_category, monthly_trend, top_vendors, budget_vs_actual, kpis } = data

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-warmgray-900">Spend Analytics</h1>
        <p className="text-sm text-warmgray-500 mt-0.5">YTD FY 2024-25 · Real-time spend cube</p>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {[
          { label: 'Avg Invoice Cycle', value: `${kpis.invoice_cycle_time_days} days` },
          { label: '3-Way Match Rate', value: `${kpis.three_way_match_rate_pct}%` },
          { label: 'Auto-Approval Rate', value: `${kpis.auto_approval_rate_pct}%` },
          { label: 'Early Pay Savings MTD', value: fmtInr(kpis.early_payment_savings_mtd) },
          { label: 'Maverick Spend', value: `${kpis.maverick_spend_pct}%`, warn: true },
          { label: 'PO Coverage', value: `${kpis.po_coverage_pct}%` },
        ].map(k => (
          <div key={k.label} className={`rounded-xl border p-3 text-center ${k.warn ? 'bg-yellow-50 border-yellow-200' : 'bg-white border-warmgray-100'}`}>
            <div className={`text-xl font-bold ${k.warn ? 'text-yellow-700' : 'text-warmgray-800'}`}>{k.value}</div>
            <div className="text-[11px] text-warmgray-500 mt-0.5 leading-tight">{k.label}</div>
          </div>
        ))}
      </div>

      {/* Charts row 1 */}
      <div className="grid grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-sm font-semibold text-warmgray-700 mb-4">Monthly Spend by Category (₹)</h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={monthly_trend} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F3F1EE" />
              <XAxis dataKey="month" tick={{ fontSize: 10, fill: '#A39E96' }} />
              <YAxis tickFormatter={v => `₹${(v/100000).toFixed(0)}L`} tick={{ fontSize: 9, fill: '#A39E96' }} />
              <Tooltip formatter={fmtInr} />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              <Bar dataKey="it" name="IT Services" fill="#D63B55" stackId="a" />
              <Bar dataKey="consulting" name="Consulting" fill="#8b5cf6" stackId="a" />
              <Bar dataKey="facilities" name="Facilities" fill="#06b6d4" stackId="a" />
              <Bar dataKey="other" name="Other" fill="#A39E96" stackId="a" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3 className="text-sm font-semibold text-warmgray-700 mb-4">Spend by Category (YTD)</h3>
          <div className="space-y-3 mt-2">
            {spend_by_category.map(c => (
              <div key={c.category}>
                <div className="flex justify-between text-xs mb-1">
                  <div className="flex gap-3">
                    <span className="font-medium text-warmgray-700">{c.category}</span>
                    <span className="text-warmgray-400">{c.invoices} invoices · {c.vendors} vendors</span>
                  </div>
                  <span className="font-bold text-warmgray-700">{fmtInr(c.amount)}</span>
                </div>
                <div className="h-2 bg-warmgray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-brand-500 rounded-full" style={{ width: `${(c.amount / 74200000 * 100).toFixed(0)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Budget vs actual */}
      <div className="card">
        <h3 className="text-sm font-semibold text-warmgray-700 mb-4">Budget vs Committed vs Actual (FY 2024-25)</h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={budget_vs_actual} margin={{ top: 5, right: 10, left: 30, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#F3F1EE" />
            <XAxis dataKey="dept" tick={{ fontSize: 10, fill: '#64748b' }} />
            <YAxis tickFormatter={v => `₹${(v/10000000).toFixed(1)}Cr`} tick={{ fontSize: 9, fill: '#A39E96' }} />
            <Tooltip formatter={fmtInr} />
            <Legend wrapperStyle={{ fontSize: '11px' }} />
            <Bar dataKey="budget" name="Total Budget" fill="#e2e8f0" />
            <Bar dataKey="actual" name="Actual Spend" fill="#D63B55" />
            <Bar dataKey="committed" name="Committed (POs)" fill="#E8899A" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Top vendors */}
      <div className="card">
        <h3 className="text-sm font-semibold text-warmgray-700 mb-4">Top Vendors by Spend</h3>
        <div className="table-wrapper">
          <table className="w-full text-sm">
            <thead className="text-warmgray-400 text-xs">
              <tr>
                <th className="text-left py-2 pr-4">#</th>
                <th className="text-left py-2">Vendor</th>
                <th className="text-right py-2">YTD Spend</th>
                <th className="text-center py-2">Invoices</th>
                <th className="text-center py-2">On-Time %</th>
                <th className="text-left py-2 pl-4">Spend Bar</th>
              </tr>
            </thead>
            <tbody>
              {top_vendors.map((v, i) => (
                <tr key={v.name} className="border-t border-warmgray-50">
                  <td className="py-2.5 pr-4 text-warmgray-400 font-bold">{i + 1}</td>
                  <td className="py-2.5 font-medium text-warmgray-800">{v.name}</td>
                  <td className="py-2.5 text-right font-bold">{fmtInr(v.amount)}</td>
                  <td className="py-2.5 text-center text-warmgray-500">{v.invoices}</td>
                  <td className="py-2.5 text-center">
                    <span className={`badge text-[11px] ${v.on_time_pct >= 98 ? 'badge-green' : v.on_time_pct >= 95 ? 'badge-yellow' : 'badge-red'}`}>
                      {v.on_time_pct}%
                    </span>
                  </td>
                  <td className="py-2.5 pl-4 w-40">
                    <div className="h-2 bg-warmgray-100 rounded-full overflow-hidden">
                      <div className="h-full bg-brand-400 rounded-full" style={{ width: `${(v.amount / top_vendors[0].amount * 100).toFixed(0)}%` }} />
                    </div>
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
