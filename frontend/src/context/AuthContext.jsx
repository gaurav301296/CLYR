import { createContext, useContext, useState, useEffect, useCallback } from 'react';

const AuthContext = createContext(null);

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8005/api';

async function apiFetch(path, options = {}) {
  const token = localStorage.getItem('access_token');
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error(data?.detail || data?.message || `Request failed (${res.status})`);
  }
  return data;
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Restore session from stored token
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setLoading(false);
      return;
    }
    apiFetch('/user/me')
      .then((profile) => {
        setUser(profile);
      })
      .catch(() => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      })
      .finally(() => setLoading(false));
  }, []);

  const signUp = useCallback(async (email, password, fullName = '') => {
    const data = await apiFetch('/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
    return data;
  }, []);

  const signIn = useCallback(async (email, password) => {
    const data = await apiFetch('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    if (data.access_token) {
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
    }
    const profile = { id: data.user?.id, email: data.user?.email };
    setUser(profile);
    return data;
  }, []);

  const signOut = useCallback(async () => {
    try {
      await apiFetch('/auth/logout', { method: 'POST' });
    } catch { /* ignore */ }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      const profile = await apiFetch('/user/me');
      setUser(profile);
      return profile;
    } catch { return null; }
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, signUp, signIn, signOut, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
