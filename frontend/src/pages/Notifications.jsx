import { useEffect, useState } from 'react'
import { getNotifications, getUnreadCount, markNotificationRead, markAllNotificationsRead } from '../api'
import { Bell, CheckCheck, Eye, RefreshCw, AlertTriangle, Info, Shield, Server, FileText } from 'lucide-react'

const SEVERITY_STYLE = {
  CRITICAL: 'border-l-red-500 bg-red-50',
  HIGH:     'border-l-orange-500 bg-orange-50',
  MEDIUM:   'border-l-yellow-500 bg-yellow-50',
  LOW:      'border-l-blue-500 bg-blue-50',
  INFO:     'border-l-warmgray-300 bg-warmgray-50',
}

const SEVERITY_BADGE = {
  CRITICAL: 'badge badge-red',
  HIGH:     'badge badge-orange',
  MEDIUM:   'badge badge-yellow',
  LOW:      'badge badge-blue',
  INFO:     'badge badge-gray',
}

const TYPE_ICON = {
  MSME_ALERT:       <AlertTriangle className="w-5 h-5 text-red-500" />,
  FRAUD_WARNING:    <Shield className="w-5 h-5 text-red-600" />,
  APPROVAL_REQUEST: <FileText className="w-5 h-5 text-brand-500" />,
  EBS_FAILURE:      <Server className="w-5 h-5 text-orange-500" />,
  GST_ISSUE:        <AlertTriangle className="w-5 h-5 text-yellow-500" />,
  SYSTEM:           <Info className="w-5 h-5 text-warmgray-500" />,
  PAYMENT_ALERT:    <Bell className="w-5 h-5 text-green-500" />,
}

export default function Notifications() {
  const [notifications, setNotifications] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [filter, setFilter] = useState('ALL')
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    Promise.all([
      getNotifications({ limit: 100 }),
      getUnreadCount(),
    ]).then(([n, u]) => {
      setNotifications(n)
      setUnreadCount(u.count)
      setLoading(false)
    }).catch(() => setLoading(false))
  }

  useEffect(load, [])

  const handleMarkRead = async (id) => {
    await markNotificationRead(id)
    load()
  }

  const handleMarkAllRead = async () => {
    await markAllNotificationsRead()
    load()
  }

  const filtered = filter === 'ALL' ? notifications
    : filter === 'UNREAD' ? notifications.filter(n => !n.is_read)
    : notifications.filter(n => n.severity === filter)

  if (loading) return <div className="flex items-center justify-center h-64 text-warmgray-400">Loading notifications…</div>

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-warmgray-900">Notifications</h1>
          <p className="text-sm text-warmgray-500 mt-0.5">System alerts, compliance warnings, approval requests</p>
        </div>
        <div className="flex gap-2">
          {unreadCount > 0 && (
            <button onClick={handleMarkAllRead} className="btn-secondary text-xs">
              <CheckCheck className="w-3.5 h-3.5" /> Mark All Read ({unreadCount})
            </button>
          )}
          <button onClick={load} className="btn-secondary text-xs">
            <RefreshCw className="w-3.5 h-3.5" /> Refresh
          </button>
        </div>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-brand-100 p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-warmgray-500 font-medium uppercase tracking-wide">Total</p>
              <p className="text-2xl font-bold text-warmgray-900 mt-1">{notifications.length}</p>
            </div>
            <div className="bg-brand-50 p-2.5 rounded-lg"><Bell className="w-5 h-5 text-brand-600" /></div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-red-100 p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-warmgray-500 font-medium uppercase tracking-wide">Unread</p>
              <p className="text-2xl font-bold text-red-600 mt-1">{unreadCount}</p>
            </div>
            <div className="bg-red-50 p-2.5 rounded-lg"><Eye className="w-5 h-5 text-red-600" /></div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-red-100 p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-warmgray-500 font-medium uppercase tracking-wide">Critical</p>
              <p className="text-2xl font-bold text-warmgray-900 mt-1">{notifications.filter(n => n.severity === 'CRITICAL').length}</p>
            </div>
            <div className="bg-red-50 p-2.5 rounded-lg"><AlertTriangle className="w-5 h-5 text-red-600" /></div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-orange-100 p-5">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-warmgray-500 font-medium uppercase tracking-wide">High Priority</p>
              <p className="text-2xl font-bold text-warmgray-900 mt-1">{notifications.filter(n => n.severity === 'HIGH').length}</p>
            </div>
            <div className="bg-orange-50 p-2.5 rounded-lg"><AlertTriangle className="w-5 h-5 text-orange-600" /></div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2 flex-wrap">
        {['ALL', 'UNREAD', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(f => (
          <button key={f}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${filter === f ? 'bg-brand-500 text-white' : 'bg-white text-warmgray-600 border border-warmgray-200 hover:bg-warmgray-50'}`}
            onClick={() => setFilter(f)}>
            {f === 'ALL' ? `All (${notifications.length})` :
             f === 'UNREAD' ? `Unread (${unreadCount})` :
             `${f} (${notifications.filter(n => n.severity === f).length})`}
          </button>
        ))}
      </div>

      {/* Notification list */}
      <div className="space-y-2">
        {filtered.length === 0 ? (
          <div className="card text-center text-warmgray-400 py-12">
            <Bell className="w-8 h-8 mx-auto mb-2 opacity-30" />
            <p className="text-sm">No notifications</p>
          </div>
        ) : filtered.map(n => (
          <div key={n.id}
            className={`rounded-xl border-l-4 border p-4 transition-all ${
              SEVERITY_STYLE[n.severity] || 'border-l-warmgray-300 bg-warmgray-50'
            } ${!n.is_read ? 'ring-1 ring-brand-200' : 'opacity-80'}`}>
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 mt-0.5">
                {TYPE_ICON[n.notification_type] || <Bell className="w-5 h-5 text-warmgray-400" />}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h4 className={`text-sm font-semibold ${!n.is_read ? 'text-warmgray-900' : 'text-warmgray-600'}`}>{n.title}</h4>
                  <span className={SEVERITY_BADGE[n.severity] || 'badge badge-gray'} style={{fontSize: '10px'}}>{n.severity}</span>
                  {!n.is_read && <span className="w-2 h-2 bg-brand-500 rounded-full flex-shrink-0"></span>}
                </div>
                <p className="text-xs text-warmgray-500 mt-1">{n.message}</p>
                <div className="flex items-center gap-3 mt-2">
                  <span className="text-[11px] text-warmgray-400 font-mono">{n.notification_type}</span>
                  <span className="text-[11px] text-warmgray-300">·</span>
                  <span className="text-[11px] text-warmgray-400">
                    {n.created_at ? new Date(n.created_at).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '—'}
                  </span>
                </div>
              </div>
              {!n.is_read && (
                <button
                  onClick={() => handleMarkRead(n.id)}
                  className="flex-shrink-0 px-2 py-1 text-xs text-brand-600 hover:bg-brand-100 rounded transition-colors">
                  Mark read
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
