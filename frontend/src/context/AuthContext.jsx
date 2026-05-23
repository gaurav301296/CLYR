import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import logger from '../lib/logger';

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
    logger.info('Restoring session from stored token');
    apiFetch('/user/me')
      .then((profile) => {
        setUser(profile);
        logger.info('Session restored', { email: profile.email });
      })
      .catch(() => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        logger.warn('Stored token invalid, cleared session');
      })
      .finally(() => setLoading(false));
  }, []);

  const signUp = useCallback(async (email, password, fullName = '') => {
    logger.info('Signup attempt', { email });
    const data = await apiFetch('/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
    logger.track('signup_success', { email });
    return data;
  }, []);

  const signIn = useCallback(async (email, password) => {
    logger.info('Login attempt', { email });
    const data = await apiFetch('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    if (data.access_token) {
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      logger.info('Login successful', { email });
      logger.track('login_success', { email });
    }
    const profile = { id: data.user?.id, email: data.user?.email, full_name: data.user?.full_name };
    setUser(profile);
    return data;
  }, []);

  const signOut = useCallback(async () => {
    logger.info('Logout');
    try {
      await apiFetch('/auth/logout', { method: 'POST' });
    } catch { /* ignore */ }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    logger.track('logout');
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
