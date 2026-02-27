import { useEffect, useState } from 'react'
import { getGSTCache, syncGST } from '../api'
import { Database, RefreshCw, CheckCircle, AlertTriangle, Clock } from 'lucide-react'

export default function GSTCache() {
  const [data, setData] = useState(null)
  const [syncing, setSyncing] = useState(false)
  const [syncResult, setSyncResult] = useState(null)
  const [filter, setFilter] = useState('ALL')

  const load = () => getGSTCache().then(setData)
  useEffect(() => { load() }, [])

  const doSync = async () => {
    setSyncing(true)
    setSyncResult(null)
    const r = await syncGST()
    setSyncResult(r)
    await load()
    setSyncing(false)
  }

  if (!data) return <div className="text-warmgray-400 py-8 text-center">Loading GST Cache…</div>

  const filtered = filter === 'ALL' ? data.records
    : filter === 'NO_GSTR2B' ? data.records.filter(r => !r.gstr2b_available)
    : filter === 'DELAYED' ? data.records.filter(r => r.gstr1_compliance === 'DELAYED')
    : data.records

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-warmgray-900">GST Data Cache</h1>
          <p className="text-sm text-warmgray-500 mt-0.5">
            Cygnet GSP data cached locally — avoids per-invoice API calls · Last full sync: <strong>{new Date(data.last_full_sync).toLocaleString('en-IN')}</strong>
          </p>
        </div>
        <button className="btn-primary" onClick={doSync} disabled={syncing}>
          <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
          {syncing ? 'Syncing with Cygnet…' : 'Sync from Cygnet GSP'}
        </button>
      </div>

      {syncResult && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-sm text-green-800">
          <div className="font-semibold">✓ Cygnet Batch Sync Complete</div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-2 text-xs">
            <div>GSTINs synced: <strong>{syncResult.total_gstins}</strong></div>
            <div>Records updated: <strong>{syncResult.records_updated}</strong></div>
            <div>Batch type: <strong>{syncResult.batch_type}</strong></div>
            <div>Provider: <strong>{syncResult.provider}</strong></div>
          </div>
          <p className="text-xs text-green-700 mt-1">{syncResult.note}</p>
        </div>
      )}

      {/* Strategy callout */}
      <div className="bg-brand-50 border border-brand-200 rounded-xl p-4 text-sm">
        <div className="font-semibold text-brand-900 mb-2 flex items-center gap-2"><Database className="w-4 h-4" /> Cygnet GSP Caching Strategy</div>
        <div className="grid grid-cols-2 gap-x-8 gap-y-1 text-xs text-brand-800">
          <div>📦 <strong>GSTIN validity + status</strong> — daily batch · 24h TTL</div>
          <div>📦 <strong>GSTR-2B (ITC data)</strong> — monthly after 14th</div>
          <div>📦 <strong>GSTR-1 filing status</strong> — weekly · 7d TTL</div>
          <div>📦 <strong>HSN/SAC master</strong> — monthly · 30d TTL</div>
          <div className="text-orange-700">⚡ <strong>IRN generation</strong> — live Cygnet call (per invoice)</div>
          <div className="text-orange-700">⚡ <strong>IRN cancellation / E-way bill</strong> — live Cygnet call</div>
        </div>
        <div className="mt-2 text-xs text-brand-600 font-medium">
          This month: {data.total_cache_hits} cache hits → {data.total_cache_hits} Cygnet API calls avoided
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {[
          { label: 'Total GSTINs', value: data.total, color: 'blue' },
          { label: 'Active Status', value: data.active, color: 'green' },
          { label: 'GSTR-2B Available', value: data.gstr2b_available, color: 'green' },
          { label: 'GSTR-2B Missing', value: data.gstr2b_missing, color: data.gstr2b_missing > 0 ? 'red' : 'green' },
          { label: 'GSTR-1 Delayed', value: data.gstr1_delayed, color: data.gstr1_delayed > 0 ? 'red' : 'green' },
        ].map(s => (
          <div key={s.label} className={`rounded-xl border p-4 text-center ${
            s.color === 'red' ? 'bg-red-50 border-red-200' :
            s.color === 'green' ? 'bg-green-50 border-green-200' : 'bg-brand-50 border-brand-200'}`}>
            <div className={`text-2xl font-bold ${s.color === 'red' ? 'text-red-700' : s.color === 'green' ? 'text-green-700' : 'text-brand-700'}`}>{s.value}</div>
            <div className="text-xs text-warmgray-500 mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Filter */}
      <div className="flex gap-2">
        {[['ALL','All'], ['NO_GSTR2B','Missing GSTR-2B'], ['DELAYED','GSTR-1 Delayed']].map(([v, l]) => (
          <button key={v}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${filter === v ? 'bg-brand-500 text-white' : 'bg-white text-warmgray-600 border border-warmgray-200 hover:bg-warmgray-50'}`}
            onClick={() => setFilter(v)}>{l}
          </button>
        ))}
      </div>

      {/* GSTIN Table */}
      <div className="card p-0 overflow-hidden">
        <div className="table-wrapper">
          <table className="w-full text-sm">
            <thead className="bg-warmgray-50 border-b border-warmgray-100">
              <tr>
                {['GSTIN','Legal Name','State','Reg Type','GSTIN Status','GSTR-1','GSTR-2B','ITC Eligible','Last Synced','Source','Hits'].map(h => (
                  <th key={h} className="px-3 py-3 text-left text-xs font-semibold text-warmgray-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-warmgray-50">
              {filtered.map(g => (
                <tr key={g.gstin} className={`text-sm ${!g.gstr2b_available || g.gstr1_compliance === 'DELAYED' ? 'bg-yellow-50' : 'hover:bg-warmgray-50'}`}>
                  <td className="px-3 py-2.5 font-mono text-xs text-brand-700">{g.gstin}</td>
                  <td className="px-3 py-2.5 text-xs text-warmgray-700 max-w-[140px] truncate">{g.legal_name}</td>
                  <td className="px-3 py-2.5 text-xs text-warmgray-500">{g.state}</td>
                  <td className="px-3 py-2.5 text-xs text-warmgray-500">{g.registration_type}</td>
                  <td className="px-3 py-2.5">
                    <span className={`badge text-[11px] ${g.status === 'ACTIVE' ? 'badge-green' : 'badge-red'}`}>
                      {g.status === 'ACTIVE' ? '✓ Active' : g.status}
                    </span>
                  </td>
                  <td className="px-3 py-2.5">
                    <span className={`badge text-[11px] ${g.gstr1_compliance === 'FILED' ? 'badge-green' : g.gstr1_compliance === 'DELAYED' ? 'badge-red' : 'badge-yellow'}`}>
                      {g.gstr1_compliance} {g.last_gstr1_filed ? `· ${g.last_gstr1_filed}` : ''}
                    </span>
                  </td>
                  <td className="px-3 py-2.5">
                    {g.gstr2b_available
                      ? <span className="badge badge-green text-[11px]">✓ {g.gstr2b_period}</span>
                      : <div>
                          <span className="badge badge-red text-[11px]">✗ Missing</span>
                          {g.gstr2b_alert && <div className="text-[11px] text-red-600 mt-0.5 max-w-[120px]">{g.gstr2b_alert}</div>}
                        </div>}
                  </td>
                  <td className="px-3 py-2.5">
                    {g.itc_eligible
                      ? <span className="text-green-700 text-xs font-medium">✓ Eligible</span>
                      : <span className="text-red-600 text-xs font-medium">✗ Not eligible</span>}
                    {g.itc_note && <div className="text-[11px] text-warmgray-400">{g.itc_note}</div>}
                  </td>
                  <td className="px-3 py-2.5 text-xs text-warmgray-400 whitespace-nowrap">
                    {new Date(g.last_synced).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
                  </td>
                  <td className="px-3 py-2.5">
                    <span className={`badge text-[11px] ${g.sync_source === 'CYGNET_BATCH' ? 'badge-blue' : 'badge-orange'}`}>
                      {g.sync_source === 'CYGNET_BATCH' ? '🔄 Batch' : '⚡ Live'}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 text-xs text-center font-medium text-warmgray-600">{g.cache_hit_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
