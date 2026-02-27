import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Building2, Lock, Mail, ArrowRight, AlertCircle } from 'lucide-react'

export default function Login() {
  const { login, isAuthenticated, loading } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-warmgray-50">
        <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (isAuthenticated) return <Navigate to="/dashboard" replace />

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await login(email, password)
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid email or password')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex">
      {/* Left panel — branding */}
      <div className="hidden lg:flex lg:w-[45%] bg-gradient-to-br from-[#1A0A10] via-[#2D1520] to-[#4A1A2E] flex-col justify-between p-12 relative overflow-hidden">
        <div className="absolute inset-0 opacity-5">
          <div className="absolute top-20 left-10 w-64 h-64 rounded-full bg-brand-400 blur-3xl" />
          <div className="absolute bottom-20 right-10 w-80 h-80 rounded-full bg-brand-600 blur-3xl" />
        </div>

        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-brand-500 rounded-xl flex items-center justify-center">
              <Building2 className="w-6 h-6 text-white" />
            </div>
            <span className="text-white text-xl font-semibold">P2P Platform</span>
          </div>
          <p className="text-warmgray-400 text-sm ml-[52px]">Procure to Pay</p>
        </div>

        <div className="relative z-10">
          <h1 className="text-white text-3xl font-semibold leading-tight mb-4">
            Enterprise Procurement,<br />Simplified.
          </h1>
          <p className="text-warmgray-400 text-sm leading-relaxed max-w-md">
            End-to-end procure-to-pay automation with AI-powered insights,
            real-time compliance monitoring, and seamless EBS integration.
          </p>

          <div className="mt-10 grid grid-cols-3 gap-6">
            {[
              { value: '22', label: 'Modules' },
              { value: '95+', label: 'API Endpoints' },
              { value: '5', label: 'AI Agents' },
            ].map((stat) => (
              <div key={stat.label}>
                <div className="text-brand-400 text-2xl font-bold">{stat.value}</div>
                <div className="text-warmgray-500 text-xs mt-0.5">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="relative z-10 text-warmgray-500 text-xs">
          &copy; 2024 P2P Platform. All rights reserved.
        </div>
      </div>

      {/* Right panel — login form */}
      <div className="flex-1 flex items-center justify-center p-6 bg-warmgray-50">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-3 mb-10">
            <div className="w-10 h-10 bg-brand-500 rounded-xl flex items-center justify-center">
              <Building2 className="w-6 h-6 text-white" />
            </div>
            <span className="text-warmgray-800 text-xl font-semibold">P2P Platform</span>
          </div>

          <h2 className="text-2xl font-semibold text-warmgray-800 mb-1">Welcome back</h2>
          <p className="text-warmgray-500 text-sm mb-8">Sign in to your account to continue</p>

          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="flex items-center gap-2 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-warmgray-700 mb-1.5">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-warmgray-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 text-sm border border-warmgray-200 rounded-lg bg-white text-warmgray-800 placeholder:text-warmgray-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition-colors"
                  placeholder="admin@p2p.demo"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-warmgray-700 mb-1.5">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-warmgray-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 text-sm border border-warmgray-200 rounded-lg bg-white text-warmgray-800 placeholder:text-warmgray-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500 transition-colors"
                  placeholder="Enter your password"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-brand-500 hover:bg-brand-600 disabled:bg-brand-300 text-white text-sm font-medium rounded-lg transition-colors"
            >
              {submitting ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  Sign in
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <div className="mt-8 p-4 bg-white border border-warmgray-100 rounded-lg">
            <p className="text-xs font-medium text-warmgray-500 mb-2">Demo Credentials</p>
            <div className="space-y-1.5 text-xs text-warmgray-600">
              <div className="flex justify-between">
                <span>Admin</span>
                <code className="text-brand-600">admin@p2p.demo / admin123</code>
              </div>
              <div className="flex justify-between">
                <span>Finance Head</span>
                <code className="text-brand-600">priya.menon@p2p.demo / password</code>
              </div>
              <div className="flex justify-between">
                <span>Dept Head</span>
                <code className="text-brand-600">amit.sharma@p2p.demo / password</code>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
