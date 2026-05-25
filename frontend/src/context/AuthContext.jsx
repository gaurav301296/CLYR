/**
 * CLYR v2 — Auth Context (Local JWT)
 * Uses local SQLite + JWT backend instead of Supabase Auth.
 * Same interface so components don't need changes.
 */
import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(undefined);

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8005/api';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check existing session on mount
  useEffect(() => {
    const token = localStorage.getItem('clyr_token');
    if (token) {
      // Verify token with backend
      fetch(`${API_BASE}/user/me`, {
        headers: { 'Authorization': `Bearer ${token}` },
      })
        .then(res => {
          if (res.ok) return res.json();
          throw new Error('Invalid token');
        })
        .then(userData => {
          setUser(userData);
          setLoading(false);
        })
        .catch(() => {
          localStorage.removeItem('clyr_token');
          localStorage.removeItem('clyr_refresh_token');
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  async function signUp(email, password, fullName) {
    const res = await fetch(`${API_BASE}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, full_name: fullName }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Signup failed' }));
      throw new Error(err.detail || 'Signup failed');
    }

    const data = await res.json();
    // Auto-login after signup
    const loginRes = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (loginRes.ok) {
      const loginData = await loginRes.json();
      localStorage.setItem('clyr_token', loginData.access_token);
      if (loginData.refresh_token) {
        localStorage.setItem('clyr_refresh_token', loginData.refresh_token);
      }
      setUser(loginData.user);
    }

    return data;
  }

  async function signIn(email, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(err.detail || 'Login failed');
    }

    const data = await res.json();
    localStorage.setItem('clyr_token', data.access_token);
    if (data.refresh_token) {
      localStorage.setItem('clyr_refresh_token', data.refresh_token);
    }
    setUser(data.user);
    return data;
  }

  async function signOut() {
    const token = localStorage.getItem('clyr_token');
    if (token) {
      try {
        await fetch(`${API_BASE}/auth/logout`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` },
        });
      } catch {
        // Ignore network errors on logout
      }
    }
    localStorage.removeItem('clyr_token');
    localStorage.removeItem('clyr_refresh_token');
    setUser(null);
  }

  const value = {
    user,
    loading,
    signUp,
    signIn,
    signOut,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
