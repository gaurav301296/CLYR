import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { identifyUser, resetAnalytics } from '../lib/analytics';
import { supabase } from '../lib/supabase';

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
        identifyUser(profile.id, { email: profile.email });
      })
      .catch(() => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        resetAnalytics();
      })
      .finally(() => setLoading(false));
  }, []);

  const signUp = useCallback(async (email, password, fullName = '') => {
    // Use Supabase if available, otherwise use backend API
    if (supabase) {
      const data = await supabase.auth.signUp({ email, password, options: { data: { full_name: fullName } } });
      return data;
    }
    return apiFetch('/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
  }, []);

  const signIn = useCallback(async (email, password) => {
    if (supabase) {
      const data = await supabase.auth.signInWithPassword({ email, password });
      if (data.session) {
        localStorage.setItem('access_token', data.session.access_token);
        localStorage.setItem('refresh_token', data.session.refresh_token);
      }
      const profile = { id: data.user?.id, email: data.user?.email };
      setUser(profile);
      identifyUser(profile.id, { email: profile.email });
      return data;
    }
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
    identifyUser(profile.id, { email: profile.email });
    return data;
  }, []);

  const signOut = useCallback(async () => {
    try {
      if (supabase) await supabase.auth.signOut();
      else await apiFetch('/auth/logout', { method: 'POST' });
    } catch { /* ignore */ }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    resetAnalytics();
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
