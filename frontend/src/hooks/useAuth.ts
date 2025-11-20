import { useState, useEffect } from 'react'

export function useAuth() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'))

  useEffect(() => {
    const stored = localStorage.getItem('token')
    setToken(stored)
  }, [])

  const login = (accessToken: string) => {
    localStorage.setItem('token', accessToken)
    setToken(accessToken)
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
  }

  return { token, login, logout }
}
