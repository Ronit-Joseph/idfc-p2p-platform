import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import api from '../api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(() => localStorage.getItem('p2p_token'))
  const [loading, setLoading] = useState(true)

  // Attach token to every request
  useEffect(() => {
    const interceptor = api.interceptors.request.use((config) => {
      const t = localStorage.getItem('p2p_token')
      if (t) config.headers.Authorization = `Bearer ${t}`
      return config
    })
    return () => api.interceptors.request.eject(interceptor)
  }, [])

  // On 401 response, clear auth
  useEffect(() => {
    const interceptor = api.interceptors.response.use(
      (res) => res,
      (err) => {
        if (err.response?.status === 401 && token) {
          localStorage.removeItem('p2p_token')
          setToken(null)
          setUser(null)
        }
        return Promise.reject(err)
      }
    )
    return () => api.interceptors.response.eject(interceptor)
  }, [token])

  // Fetch user profile on mount if token exists
  useEffect(() => {
    if (!token) {
      setLoading(false)
      return
    }
    api.get('/auth/me')
      .then((res) => setUser(res.data))
      .catch(() => {
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
    setToken(access_token)
    setUser(userData)
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
