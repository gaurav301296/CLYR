/**
 * CLYR v2 — Auth Context (Local JWT)
 * Uses local SQLite + JWT backend instead of Supabase Auth.
 * Same interface so components don't need changes.
 */
import { createContext, useContext, useState, useEffect } from 'react';
import { apiFetch } from '../api/client';

const AuthContext = createContext(undefined);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check existing session on mount
  useEffect(() => {
    const token = localStorage.getItem('clyr_token');
    if (token) {
      apiFetch('/user/me')
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
    const data = await apiFetch('/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName }),
    });

    // Auto-login after signup
    try {
      const loginData = await apiFetch('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      localStorage.setItem('clyr_token', loginData.access_token);
      if (loginData.refresh_token) {
        localStorage.setItem('clyr_refresh_token', loginData.refresh_token);
      }
      setUser(loginData.user);
    } catch {
      // Signup succeeded but auto-login failed — user can log in manually
    }

    return data;
  }

  async function signIn(email, password) {
    const data = await apiFetch('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    localStorage.setItem('clyr_token', data.access_token);
    if (data.refresh_token) {
      localStorage.setItem('clyr_refresh_token', data.refresh_token);
    }
    setUser(data.user);
    return data;
  }

  async function signOut() {
    try {
      await apiFetch('/auth/logout', { method: 'POST' });
    } catch {
      // Ignore network errors on logout
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
