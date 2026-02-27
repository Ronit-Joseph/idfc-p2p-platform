import { useState } from 'react'
import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import {
  LayoutDashboard, FileText, ShoppingCart, Receipt, Database,
  AlertTriangle, Server, Bot, BarChart3, Users, ChevronRight,
  Building2, Bell, Settings, LogOut, Menu, X,
  Scale, CreditCard, Calculator, FolderOpen, GitBranch, ScrollText,
  FileSignature, Search
} from 'lucide-react'

const NAV_GROUPS = [
  {
    label: 'CORE P2P',
    items: [
      { to: '/dashboard',          icon: LayoutDashboard, label: 'Dashboard' },
      { to: '/purchase-requests',  icon: FileText,        label: 'Purchase Requests' },
      { to: '/purchase-orders',    icon: ShoppingCart,     label: 'Purchase Orders' },
      { to: '/invoices',           icon: Receipt,          label: 'Invoices' },
      { to: '/matching',           icon: Scale,            label: 'Matching Engine' },
      { to: '/payments',           icon: CreditCard,       label: 'Payments' },
      { to: '/tds',                icon: Calculator,       label: 'TDS Management' },
    ]
  },
  {
    label: 'PROCUREMENT',
    items: [
      { to: '/contracts',          icon: FileSignature,    label: 'Contracts' },
      { to: '/sourcing',           icon: Search,           label: 'Sourcing / RFQ' },
    ]
  },
  {
    label: 'COMPLIANCE',
    items: [
      { to: '/gst-cache',          icon: Database,         label: 'GST Cache',        badge: '3', badgeColor: 'yellow' },
      { to: '/msme',               icon: AlertTriangle,    label: 'MSME Compliance',  badge: '2', badgeColor: 'red' },
      { to: '/ebs',                icon: Server,           label: 'Oracle EBS Sync',  badge: '1', badgeColor: 'red' },
    ]
  },
  {
    label: 'OPERATIONS',
    items: [
      { to: '/workflow',           icon: GitBranch,        label: 'Workflow' },
      { to: '/documents',          icon: FolderOpen,       label: 'Documents' },
      { to: '/notifications',      icon: Bell,             label: 'Notifications' },
      { to: '/audit',              icon: ScrollText,       label: 'Audit Trail' },
    ]
  },
  {
    label: 'INTELLIGENCE',
    items: [
      { to: '/ai-agents',          icon: Bot,              label: 'AI Agents' },
      { to: '/analytics',          icon: BarChart3,        label: 'Spend Analytics' },
      { to: '/suppliers',          icon: Users,            label: 'Suppliers' },
    ]
  },
]

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const initials = user?.full_name
    ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : 'U'
  const displayName = user?.full_name || 'User'
  const displayRole = user?.role?.replace(/_/g, ' ') || 'User'

  return (
    <div className="flex h-screen overflow-hidden bg-warmgray-50">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 bg-black/50 md:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-sidebar-bg flex flex-col transform transition-transform duration-200 ease-in-out
        md:relative md:translate-x-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        {/* Logo */}
        <div className="px-5 py-4 border-b border-sidebar-border">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-brand-500 rounded-lg flex items-center justify-center">
                <Building2 className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="text-white font-semibold text-sm leading-tight">P2P Platform</div>
                <div className="text-warmgray-400 text-xs">Procure to Pay</div>
              </div>
            </div>
            <button className="md:hidden text-warmgray-400 hover:text-white" onClick={() => setSidebarOpen(false)}>
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-3 overflow-y-auto">
          {NAV_GROUPS.map((group, gi) => (
            <div key={group.label} className={gi > 0 ? 'mt-4' : ''}>
              <div className="px-3 mb-1.5 text-[10px] font-semibold uppercase tracking-widest text-warmgray-500">
                {group.label}
              </div>
              <div className="space-y-0.5">
                {group.items.map(item => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    onClick={() => setSidebarOpen(false)}
                    className={({ isActive }) =>
                      `flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors ${
                        isActive
                          ? 'bg-brand-600 text-white'
                          : 'text-warmgray-400 hover:bg-sidebar-hover hover:text-white'
                      }`
                    }
                  >
                    <span className="flex items-center gap-3">
                      <item.icon className="w-4 h-4 flex-shrink-0" />
                      {item.label}
                    </span>
                    {item.badge && (
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${
                        item.badgeColor === 'red' ? 'bg-red-500 text-white' : 'bg-amber-500 text-warmgray-900'
                      }`}>
                        {item.badge}
                      </span>
                    )}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>

        {/* Bottom user */}
        <div className="px-3 py-3 border-t border-sidebar-border">
          <div className="flex items-center gap-3 px-3 py-2">
            <div className="w-8 h-8 bg-brand-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
              {initials}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-white text-xs font-medium truncate">{displayName}</div>
              <div className="text-warmgray-500 text-[11px] capitalize">{displayRole.toLowerCase()}</div>
            </div>
            <button onClick={handleLogout} className="text-warmgray-500 hover:text-warmgray-300 transition-colors" title="Sign out">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="bg-white border-b border-warmgray-100 px-4 md:px-6 py-3 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-3">
            <button className="md:hidden text-warmgray-500 hover:text-warmgray-700" onClick={() => setSidebarOpen(true)}>
              <Menu className="w-5 h-5" />
            </button>
            <div className="text-sm text-warmgray-500">
              <Breadcrumb />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex text-[11px] text-warmgray-400 bg-warmgray-50 border border-warmgray-100 rounded-full px-3 py-1 items-center gap-1.5">
              <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></span>
              All systems operational
            </div>
            <NavLink to="/notifications" className="relative p-2 text-warmgray-400 hover:text-warmgray-700 transition-colors">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-brand-500 rounded-full"></span>
            </NavLink>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-7xl mx-auto px-4 md:px-6 py-6">
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
      <span className="text-warmgray-400">P2P</span>
      {parts.map((p, i) => (
        <span key={i} className="flex items-center gap-1">
          <ChevronRight className="w-3 h-3 text-warmgray-300" />
          <span className={i === parts.length - 1 ? 'text-warmgray-700 font-medium capitalize' : 'text-warmgray-400 capitalize'}>
            {p.replace(/-/g, ' ')}
          </span>
        </span>
      ))}
    </span>
  )
}
