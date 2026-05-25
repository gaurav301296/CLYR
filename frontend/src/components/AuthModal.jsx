/**
 * CLYR v2 — Auth Modal
 * Sign up / Sign in modal with Supabase Auth.
 */
import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { X, Mail, Lock, User, AlertCircle } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8005/api';

export default function AuthModal({ onClose, initialMode = 'signup' }) {
  const [mode, setMode] = useState(initialMode); // 'signup' | 'login' | 'forgot'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');

  const { signUp, signIn } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (mode === 'signup') {
        await signUp(email, password, fullName);
        setSuccess('Check your email for a confirmation link.');
      } else if (mode === 'login') {
        await signIn(email, password);
        onClose();
      } else if (mode === 'forgot') {
        // Forgot password — call backend (placeholder for now)
        setSuccess('Password reset link sent to your email (if account exists).');
      }
    } catch (err) {
      setError(err.message || 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-label="Authentication">
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} aria-label="Close">×</button>

        <h2 className="modal-title">
          {mode === 'signup' ? 'Account Banao' : mode === 'login' ? 'Sign In Karo' : 'Password Reset Karo'}
        </h2>

        {error && (
          <div className="modal-error" role="alert">
            <AlertCircle size={16} /> {error}
          </div>
        )}

        {success && (
          <div className="modal-success" role="status">
            ✓ {success}
          </div>
        )}

        <form onSubmit={handleSubmit} className="modal-form">
          {mode === 'signup' && (
            <div className="form-group">
              <label htmlFor="auth-name">Naam</label>
              <div className="input-wrap">
                <User size={16} className="input-icon" />
                <input id="auth-name" type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Apna naam likho" />
              </div>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="auth-email">Email</label>
            <div className="input-wrap">
              <Mail size={16} className="input-icon" />
              <input id="auth-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email@example.com" required />
            </div>
          </div>

          {mode !== 'forgot' && (
            <div className="form-group">
              <label htmlFor="auth-password">Password</label>
              <div className="input-wrap">
                <Lock size={16} className="input-icon" />
                <input id="auth-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Min 8 characters" required minLength={8} />
              </div>
            </div>
          )}

          <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
            {loading ? <><span className="spinner" /> Loading...</> : mode === 'signup' ? 'Sign Up' : mode === 'login' ? 'Sign In' : 'Reset Link Bhejo'}
          </button>
        </form>

        <div className="modal-switch">
          {mode === 'signup' ? (
            <p>Account hai? <button className="link-btn" onClick={() => { setMode('login'); setError(''); }}>Sign In Karo</button></p>
          ) : mode === 'login' ? (
            <>
              <p>Naya user? <button className="link-btn" onClick={() => { setMode('signup'); setError(''); }}>Sign Up Karo</button></p>
              <p><button className="link-btn" onClick={() => { setMode('forgot'); setError(''); }}>Password Bhool Gaye?</button></p>
            </>
          ) : (
            <p><button className="link-btn" onClick={() => { setMode('login'); setError(''); }}>Wapas Sign In Karo</button></p>
          )}
        </div>
      </div>
    </div>
  );
}
