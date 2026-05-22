import { useState, useEffect, useRef, useMemo } from 'react';
import { X, Mail, Lock, User, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { trackEvent } from '../lib/analytics';
import { validateEmail, validatePassword, validateRequired } from '../lib/validation';

export default function AuthModal({ onClose }) {
  const { signUp, signIn } = useAuth();
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const modalRef = useRef(null);
  const firstInputRef = useRef(null);

  // Per-field validation errors
  const [fieldErrors, setFieldErrors] = useState({ email: '', password: '', fullName: '' });
  const [touched, setTouched] = useState({ email: false, password: false, fullName: false });

  // Validate individual fields on change
  const validateField = (name, value) => {
    let result;
    switch (name) {
      case 'email':
        result = validateEmail(value);
        break;
      case 'password':
        result = validatePassword(value);
        break;
      case 'fullName':
        result = validateRequired(value, 'Full name');
        break;
      default:
        result = { valid: true, error: '' };
    }
    setFieldErrors(prev => ({ ...prev, [name]: result.error }));
    return result.valid;
  };

  const handleBlur = (name, value) => {
    setTouched(prev => ({ ...prev, [name]: true }));
    validateField(name, value);
  };

  const handleChange = (name, value, setter) => {
    setter(value);
    if (touched[name]) {
      validateField(name, value);
    }
  };

  // Determine if the form is valid for the current mode
  const isFormValid = useMemo(() => {
    const emailValid = validateEmail(email).valid;
    const passwordValid = validatePassword(password).valid;
    if (mode === 'signup') {
      const nameValid = validateRequired(fullName, 'Full name').valid;
      return emailValid && passwordValid && nameValid;
    }
    return emailValid && passwordValid;
  }, [email, password, fullName, mode]);

  // Focus trap: focus first input on mount
  useEffect(() => {
    firstInputRef.current?.focus();
  }, [mode]);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  // Clear messages and errors when switching modes
  const switchMode = () => {
    setMode(mode === 'signup' ? 'login' : 'signup');
    setError(null);
    setSuccess(null);
    setFieldErrors({ email: '', password: '', fullName: '' });
    setTouched({ email: false, password: false, fullName: false });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Mark all fields as touched
    setTouched({ email: true, password: true, fullName: mode === 'signup' });

    // Validate all fields
    const emailValid = validateField('email', email);
    const passwordValid = validateField('password', password);
    const nameValid = mode === 'signup' ? validateField('fullName', fullName) : true;

    if (!emailValid || !passwordValid || !nameValid) {
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      if (mode === 'signup') {
        await signUp(email, password, fullName);
        setSuccess('Account created! You can now sign in.');
        trackEvent('signup_success', { email });
        setTimeout(() => {
          setMode('login');
          setSuccess(null);
          setPassword('');
        }, 2000);
      } else {
        await signIn(email, password);
        trackEvent('login_success', { email });
        onClose();
      }
    } catch (err) {
      const msg = err.message || 'Authentication failed';
      setError(msg);
      trackEvent('auth_error', { mode, error: msg });
    } finally {
      setLoading(false);
    }
  };

  const inputStyle = (hasError) => ({
    width: '100%',
    padding: '12px 12px 12px 42px',
    borderRadius: '8px',
    border: `1px solid ${hasError ? '#ef4444' : 'var(--border)'}`,
    background: 'var(--bg)',
    color: 'var(--text-highlight)',
    fontSize: '14px',
    outline: 'none',
  });

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="auth-modal-title"
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)',
      }}
      onClick={onClose}
    >
      <div
        ref={modalRef}
        className="card"
        style={{ width: '100%', maxWidth: '420px', padding: '32px', position: 'relative' }}
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          style={{ position: 'absolute', top: '16px', right: '16px', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
          aria-label="Close dialog"
        >
          <X size={20} />
        </button>

        <h2 id="auth-modal-title" style={{ fontSize: '20px', marginBottom: '8px' }}>
          {mode === 'signup' ? 'Create Account' : 'Welcome Back'}
        </h2>
        <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '24px' }}>
          {mode === 'signup' ? 'Sign up to save your credit reports and track progress.' : 'Sign in to access your reports.'}
        </p>

        {/* Error Banner */}
        {error && (
          <div
            className="error-banner"
            style={{
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 14px',
              borderRadius: '8px',
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#fca5a5',
              fontSize: '13px',
            }}
            role="alert"
          >
            <AlertCircle size={16} style={{ flexShrink: 0 }} aria-hidden="true" />
            <span>{error}</span>
          </div>
        )}

        {/* Success Banner */}
        {success && (
          <div
            style={{
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 14px',
              borderRadius: '8px',
              background: 'rgba(34, 197, 94, 0.1)',
              border: '1px solid rgba(34, 197, 94, 0.3)',
              color: '#86efac',
              fontSize: '13px',
            }}
            role="status"
          >
            <CheckCircle size={16} style={{ flexShrink: 0 }} aria-hidden="true" />
            <span>{success}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }} noValidate>
          {mode === 'signup' && (
            <div>
              <div style={{ position: 'relative' }}>
                <User size={16} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} aria-hidden="true" />
                <input
                  ref={firstInputRef}
                  type="text"
                  placeholder="Full Name"
                  value={fullName}
                  onChange={(e) => handleChange('fullName', e.target.value, setFullName)}
                  onBlur={(e) => handleBlur('fullName', e.target.value)}
                  disabled={loading}
                  aria-label="Full name"
                  aria-invalid={touched.fullName && !!fieldErrors.fullName}
                  aria-describedby={touched.fullName && fieldErrors.fullName ? 'fullName-error' : undefined}
                  style={inputStyle(touched.fullName && fieldErrors.fullName)}
                />
              </div>
              {touched.fullName && fieldErrors.fullName && (
                <p id="fullName-error" style={{ color: '#ef4444', fontSize: '12px', marginTop: '4px', marginBottom: 0 }} role="alert">{fieldErrors.fullName}</p>
              )}
            </div>
          )}
          <div>
            <div style={{ position: 'relative' }}>
              <Mail size={16} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} aria-hidden="true" />
              <input
                ref={mode === 'login' ? firstInputRef : undefined}
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => handleChange('email', e.target.value, setEmail)}
                onBlur={(e) => handleBlur('email', e.target.value)}
                disabled={loading}
                aria-label="Email address"
                aria-invalid={touched.email && !!fieldErrors.email}
                aria-describedby={touched.email && fieldErrors.email ? 'email-error' : undefined}
                autoComplete="email"
                style={inputStyle(touched.email && fieldErrors.email)}
              />
            </div>
            {touched.email && fieldErrors.email && (
              <p id="email-error" style={{ color: '#ef4444', fontSize: '12px', marginTop: '4px', marginBottom: 0 }} role="alert">{fieldErrors.email}</p>
            )}
          </div>
          <div>
            <div style={{ position: 'relative' }}>
              <Lock size={16} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} aria-hidden="true" />
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => handleChange('password', e.target.value, setPassword)}
                onBlur={(e) => handleBlur('password', e.target.value)}
                disabled={loading}
                aria-label="Password"
                aria-invalid={touched.password && !!fieldErrors.password}
                aria-describedby={touched.password && fieldErrors.password ? 'password-error' : undefined}
                autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
                style={inputStyle(touched.password && fieldErrors.password)}
              />
            </div>
            {touched.password && fieldErrors.password && (
              <p id="password-error" style={{ color: '#ef4444', fontSize: '12px', marginTop: '4px', marginBottom: 0 }} role="alert">{fieldErrors.password}</p>
            )}
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading || !isFormValid}
            aria-busy={loading}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              opacity: (loading || !isFormValid) ? 0.5 : 1,
              cursor: (loading || !isFormValid) ? 'not-allowed' : 'pointer',
            }}
          >
            {loading && <Loader2 size={16} className="animate-spin" aria-hidden="true" />}
            {loading
              ? mode === 'signup' ? 'Creating Account...' : 'Signing In...'
              : mode === 'signup' ? 'Create Account' : 'Sign In'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: '16px', fontSize: '13px', color: 'var(--text-muted)' }}>
          {mode === 'signup' ? 'Already have an account?' : "Don't have an account?"}{' '}
          <button
            onClick={switchMode}
            disabled={loading}
            style={{ background: 'none', border: 'none', color: 'var(--primary-hover)', cursor: 'pointer', fontSize: '13px' }}
            aria-label={mode === 'signup' ? 'Switch to sign in' : 'Switch to sign up'}
          >
            {mode === 'signup' ? 'Sign In' : 'Sign Up'}
          </button>
        </p>
      </div>
    </div>
  );
}
