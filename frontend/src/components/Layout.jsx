import { Outlet, NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, FileText, ShoppingCart, Receipt, Database,
  AlertTriangle, Server, Bot, BarChart3, Users, ChevronRight,
  Building2, Bell, Settings, HelpCircle, LogOut,
  Scale, CreditCard, Calculator, FolderOpen, GitBranch, ScrollText
} from 'lucide-react'

const NAV = [
  { to: '/dashboard',          icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/purchase-requests',  icon: FileText,        label: 'Purchase Requests' },
  { to: '/purchase-orders',    icon: ShoppingCart,    label: 'Purchase Orders' },
  { to: '/invoices',           icon: Receipt,         label: 'Invoice Management' },
  { to: '/matching',           icon: Scale,           label: 'Matching Engine' },
  { to: '/payments',           icon: CreditCard,      label: 'Payments' },
  { to: '/tds',                icon: Calculator,      label: 'TDS Management' },
  { label: 'divider' },
  { to: '/gst-cache',          icon: Database,        label: 'GST Cache',        badge: '3', badgeColor: 'yellow' },
  { to: '/msme',               icon: AlertTriangle,   label: 'MSME Compliance',  badge: '2', badgeColor: 'red' },
  { to: '/ebs',                icon: Server,          label: 'Oracle EBS Sync',  badge: '1', badgeColor: 'red' },
  { label: 'divider' },
  { to: '/workflow',           icon: GitBranch,       label: 'Workflow' },
  { to: '/documents',          icon: FolderOpen,      label: 'Documents' },
  { to: '/notifications',      icon: Bell,            label: 'Notifications' },
  { to: '/audit',              icon: ScrollText,      label: 'Audit Trail' },
  { label: 'divider' },
  { to: '/ai-agents',          icon: Bot,             label: 'AI Agents' },
  { to: '/analytics',          icon: BarChart3,       label: 'Spend Analytics' },
  { to: '/suppliers',          icon: Users,           label: 'Suppliers' },
]

export default function Layout() {
  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 bg-gray-900 flex flex-col">
        {/* Logo */}
        <div className="px-5 py-4 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <Building2 className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="text-white font-semibold text-sm leading-tight">P2P Platform</div>
              <div className="text-gray-400 text-xs">Procure to Pay</div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 overflow-y-auto space-y-0.5">
          {NAV.map((item, i) => {
            if (item.label === 'divider') {
              return <div key={i} className="my-3 border-t border-gray-700" />
            }
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors group ${
                    isActive
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                  }`
                }
              >
                <span className="flex items-center gap-3">
                  <item.icon className="w-4 h-4 flex-shrink-0" />
                  {item.label}
                </span>
                {item.badge && (
                  <span className={`text-xs font-bold px-1.5 py-0.5 rounded-full ${
                    item.badgeColor === 'red' ? 'bg-red-500 text-white' : 'bg-yellow-500 text-gray-900'
                  }`}>
                    {item.badge}
                  </span>
                )}
              </NavLink>
            )
          })}
        </nav>

        {/* Bottom user */}
        <div className="px-3 py-3 border-t border-gray-700 space-y-0.5">
          <button className="w-full flex items-center gap-3 px-3 py-2 text-gray-400 hover:bg-gray-800 hover:text-white rounded-lg text-sm transition-colors">
            <Settings className="w-4 h-4" /> Settings
          </button>
          <div className="flex items-center gap-3 px-3 py-2">
            <div className="w-7 h-7 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold">P</div>
            <div className="flex-1 min-w-0">
              <div className="text-white text-xs font-medium truncate">Priya Menon</div>
              <div className="text-gray-500 text-xs">Head — Procurement</div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Breadcrumb />
          </div>
          <div className="flex items-center gap-3">
            <div className="text-xs text-gray-400 bg-gray-100 rounded-full px-3 py-1">
              All systems operational
            </div>
            <NavLink to="/notifications" className="relative p-2 text-gray-500 hover:text-gray-700">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            </NavLink>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-7xl mx-auto px-6 py-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}

function Breadcrumb() {
  const loc = useLocation()
  const parts = loc.pathname.split('/').filter(Boolean)
  return (
    <span className="flex items-center gap-1">
      <span className="text-gray-400">P2P</span>
      {parts.map((p, i) => (
        <span key={i} className="flex items-center gap-1">
          <ChevronRight className="w-3 h-3 text-gray-300" />
          <span className={i === parts.length - 1 ? 'text-gray-700 font-medium capitalize' : 'text-gray-400 capitalize'}>
            {p.replace(/-/g, ' ')}
          </span>
        </span>
      ))}
    </span>
  )
}
