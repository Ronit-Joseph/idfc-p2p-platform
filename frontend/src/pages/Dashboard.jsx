import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getDashboard } from '../api'
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, Legend
} from 'recharts'
import {
  Receipt, ShoppingCart, Users, TrendingUp,
  AlertTriangle, Server, Shield, Database, Clock,
  ArrowUpRight, RefreshCw
} from 'lucide-react'

function StatCard({ icon: Icon, label, value, sub, color = 'blue', onClick }) {
  const colors = {
    blue:   { bg: 'bg-blue-50',   icon: 'text-blue-600',   border: 'border-blue-100' },
    green:  { bg: 'bg-green-50',  icon: 'text-green-600',  border: 'border-green-100' },
    yellow: { bg: 'bg-yellow-50', icon: 'text-yellow-600', border: 'border-yellow-100' },
    red:    { bg: 'bg-red-50',    icon: 'text-red-600',    border: 'border-red-100' },
    purple: { bg: 'bg-purple-50', icon: 'text-purple-600', border: 'border-purple-100' },
  }
  const c = colors[color] || colors.blue
  return (
    <div
      className={`bg-white rounded-xl border ${c.border} p-5 cursor-pointer hover:shadow-md transition-shadow`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">{label}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
        </div>
        <div className={`${c.bg} p-2.5 rounded-lg`}>
          <Icon className={`w-5 h-5 ${c.icon}`} />
        </div>
      </div>
    </div>
  )
}

const fmtInr = (v) => {
  if (!v && v !== 0) return '—'
  if (v >= 10000000) return `₹${(v/10000000).toFixed(1)}Cr`
  if (v >= 100000)   return `₹${(v/100000).toFixed(1)}L`
  return `₹${v.toLocaleString('en-IN')}`
}

const alertStyle = {
  CRITICAL: 'bg-red-50 border-red-200 text-red-800',
  WARNING:  'bg-yellow-50 border-yellow-200 text-yellow-800',
  ERROR:    'bg-red-50 border-red-200 text-red-800',
  INFO:     'bg-blue-50 border-blue-200 text-blue-800',
}
const alertIcon = { CRITICAL: '🚨', WARNING: '⚠️', ERROR: '❌', INFO: 'ℹ️' }

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const nav = useNavigate()

  const load = () => {
    setLoading(true)
    getDashboard().then(d => { setData(d); setLoading(false) }).catch(() => setLoading(false))
  }
  useEffect(load, [])

  if (loading) return <div className="flex items-center justify-center h-64 text-gray-400">Loading dashboard…</div>
  if (!data) return <div className="text-red-500 p-4">Failed to load. Is the backend running?</div>

  const { stats, alerts, monthly_trend, spend_by_category, activity, budget_utilization } = data

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Procurement Dashboard</h1>
          <p className="text-sm text-gray-500 mt-0.5">September 2024 · FY 2024-25</p>
        </div>
        <button onClick={load} className="btn-secondary text-xs">
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </button>
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="space-y-2">
          {alerts.map((a, i) => (
            <div key={i}
              onClick={() => nav(a.link)}
              className={`flex items-center gap-3 px-4 py-2.5 rounded-lg border text-sm cursor-pointer hover:opacity-90 transition-opacity ${alertStyle[a.type]}`}>
              <span>{alertIcon[a.type]}</span>
              <span className="flex-1 font-medium">{a.msg}</span>
              <ArrowUpRight className="w-4 h-4 opacity-60" />
            </div>
          ))}
        </div>
      )}

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Receipt}      label="Invoices Pending"    value={stats.invoices_pending}      sub="Awaiting approval"              color="blue"   onClick={() => nav('/invoices')} />
        <StatCard icon={TrendingUp}   label="MTD Spend"           value={stats.mtd_spend_fmt}         sub="Sep 2024"                       color="green"  onClick={() => nav('/analytics')} />
        <StatCard icon={ShoppingCart} label="Active POs"          value={stats.active_pos}            sub={`${stats.prs_pending} PRs pending`} color="purple" onClick={() => nav('/purchase-orders')} />
        <StatCard icon={Users}        label="Active Suppliers"    value={stats.active_suppliers}      sub="15 registered"                  color="blue"   onClick={() => nav('/suppliers')} />
      </div>

      <div className="grid grid-cols-3 lg:grid-cols-6 gap-4">
        <div className={`col-span-3 lg:col-span-2 rounded-xl border p-4 cursor-pointer hover:shadow-md transition-shadow ${stats.msme_at_risk_count > 0 ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'}`} onClick={() => nav('/msme')}>
          <div className="flex items-center gap-2 text-sm font-semibold text-gray-700"><AlertTriangle className="w-4 h-4 text-red-500" /> MSME Compliance</div>
          <div className="text-2xl font-bold mt-1">{stats.msme_at_risk_count}</div>
          <div className="text-xs text-gray-500">at risk / in breach</div>
        </div>
        <div className={`col-span-3 lg:col-span-2 rounded-xl border p-4 cursor-pointer hover:shadow-md transition-shadow ${stats.ebs_failures > 0 ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'}`} onClick={() => nav('/ebs')}>
          <div className="flex items-center gap-2 text-sm font-semibold text-gray-700"><Server className="w-4 h-4 text-blue-500" /> Oracle EBS Sync</div>
          <div className="text-2xl font-bold mt-1">{stats.ebs_failures}</div>
          <div className="text-xs text-gray-500">failed postings</div>
        </div>
        <div className="col-span-3 lg:col-span-2 rounded-xl border bg-blue-50 border-blue-200 p-4 cursor-pointer hover:shadow-md transition-shadow" onClick={() => nav('/gst-cache')}>
          <div className="flex items-center gap-2 text-sm font-semibold text-gray-700"><Database className="w-4 h-4 text-blue-500" /> GST Cache</div>
          <div className="text-2xl font-bold mt-1">{(stats.gst_cache_age_hours).toFixed(1)}h</div>
          <div className="text-xs text-gray-500">since last Cygnet sync</div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Monthly trend */}
        <div className="lg:col-span-2 card">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Monthly Spend Trend (₹)</h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={monthly_trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#94a3b8' }} />
              <YAxis tickFormatter={v => `₹${(v/100000).toFixed(0)}L`} tick={{ fontSize: 10, fill: '#94a3b8' }} />
              <Tooltip formatter={(v) => fmtInr(v)} />
              <Line type="monotone" dataKey="spend" stroke="#2563eb" strokeWidth={2.5} dot={{ fill: '#2563eb', r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Spend by category */}
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Spend by Category (YTD)</h3>
          <div className="space-y-3">
            {spend_by_category.map(c => (
              <div key={c.category}>
                <div className="flex justify-between text-xs text-gray-600 mb-1">
                  <span className="truncate">{c.category}</span>
                  <span className="font-medium">{c.pct}%</span>
                </div>
                <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 rounded-full" style={{ width: `${c.pct}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Budget + Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Budget utilization */}
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Budget Utilization by Department</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={budget_utilization} layout="vertical" margin={{ left: 60 }}>
              <XAxis type="number" tickFormatter={v => `${v}%`} tick={{ fontSize: 10, fill: '#94a3b8' }} domain={[0, 100]} />
              <YAxis type="category" dataKey="dept" tick={{ fontSize: 10, fill: '#64748b' }} width={60} />
              <Tooltip formatter={(v, n) => n === 'utilization_pct' ? `${v}%` : fmtInr(v)} />
              <Bar dataKey="utilization_pct" fill="#3b82f6" radius={[0, 3, 3, 0]} label={{ position: 'right', formatter: v => `${v}%`, fontSize: 10, fill: '#64748b' }} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Activity feed */}
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Recent Activity</h3>
          <div className="space-y-3">
            {activity.map((a, i) => (
              <div key={i} className="flex gap-3 text-sm">
                <div className="w-2 h-2 rounded-full mt-1.5 flex-shrink-0 bg-blue-400"></div>
                <div>
                  <p className="text-gray-700 leading-snug">{a.msg}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{new Date(a.time).toLocaleString('en-IN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
