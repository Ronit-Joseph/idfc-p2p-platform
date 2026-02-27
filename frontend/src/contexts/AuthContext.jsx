import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react'
import api from '../api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(() => localStorage.getItem('p2p_token'))
  const [loading, setLoading] = useState(true)
  const skipMeRef = useRef(false)

  // Attach token to every request
  useEffect(() => {
    const interceptor = api.interceptors.request.use((config) => {
      const t = localStorage.getItem('p2p_token')
      if (t) config.headers.Authorization = `Bearer ${t}`
      return config
    })
    return () => api.interceptors.request.eject(interceptor)
  }, [])

  // On 401 response, clear auth (but not for /auth/login or /auth/me calls)
  useEffect(() => {
    const interceptor = api.interceptors.response.use(
      (res) => res,
      (err) => {
        const url = err.config?.url || ''
        if (err.response?.status === 401 && token && !url.includes('/auth/login')) {
          localStorage.removeItem('p2p_token')
          setToken(null)
          setUser(null)
        }
        return Promise.reject(err)
      }
    )
    return () => api.interceptors.response.eject(interceptor)
  }, [token])

  // Restore session on mount only (not on every token change)
  useEffect(() => {
    if (!token) {
      setLoading(false)
      return
    }
    // If login() just set the token, skip the /me call
    if (skipMeRef.current) {
      skipMeRef.current = false
      setLoading(false)
      return
    }
    api.get('/auth/me')
      .then((res) => setUser(res.data))
      .catch(() => {
        // Token invalid or /me failed — clear session
        localStorage.removeItem('p2p_token')
        setToken(null)
        setUser(null)
      })
      .finally(() => setLoading(false))
  }, [token])

  const login = useCallback(async (email, password) => {
    const res = await api.post('/auth/login', { email, password })
    const { access_token, user: userData } = res.data
    localStorage.setItem('p2p_token', access_token)
    // Skip the /me call since we already have user data from login response
    skipMeRef.current = true
    setUser(userData)
    setToken(access_token)
    return userData
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('p2p_token')
    setToken(null)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
