import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { User, Mail, LogOut, Loader2, FileText, AlertCircle } from 'lucide-react';

export default function ProfilePage() {
  const { user, signOut, refreshUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    refreshUser()
      .then((p) => {
        setProfile(p);
        setLoading(false);
      })
      .catch(() => {
        setError('Failed to load profile');
        setLoading(false);
      });
  }, []);

  const handleLogout = async () => {
    await signOut();
  };

  if (loading) {
    return (
      <div className="uploader-card" style={{ maxWidth: '640px', marginTop: '60px', margin: '60px auto 0', textAlign: 'center' }} role="status" aria-live="polite">
        <Loader2 size={32} className="animate-spin" style={{ margin: '0 auto 16px' }} aria-hidden="true" />
        <p style={{ color: 'var(--text-muted)' }}>Loading profile...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="uploader-card" style={{ maxWidth: '640px', marginTop: '60px', margin: '60px auto 0' }} role="alert">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#fca5a5' }}>
          <AlertCircle size={20} aria-hidden="true" />
          <span>{error}</span>
        </div>
      </div>
    );
  }

  const displayName = profile?.full_name || profile?.name || user?.email?.split('@')[0] || 'User';
  const displayEmail = profile?.email || user?.email || '';

  return (
    <div style={{ maxWidth: '640px', margin: '40px auto 0', padding: '0 20px' }}>
      <h1 style={{ fontSize: '24px', marginBottom: '24px' }}>My Profile</h1>

      <div className="card" style={{ padding: '32px', marginBottom: '24px' }}>
        {/* Avatar */}
        <div style={{
          width: '72px', height: '72px', borderRadius: '50%',
          background: 'linear-gradient(135deg, var(--primary), var(--primary-hover))',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          marginBottom: '20px',
        }}>
          <User size={32} color="#fff" aria-hidden="true" />
        </div>

        {/* Name */}
        <div style={{ marginBottom: '16px' }}>
          <label style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'block', marginBottom: '4px' }}>
            Full Name
          </label>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <User size={16} color="var(--text-muted)" aria-hidden="true" />
            <span style={{ fontSize: '16px', color: 'var(--text-highlight)' }}>{displayName}</span>
          </div>
        </div>

        {/* Email */}
        <div style={{ marginBottom: '24px' }}>
          <label style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'block', marginBottom: '4px' }}>
            Email
          </label>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Mail size={16} color="var(--text-muted)" aria-hidden="true" />
            <span style={{ fontSize: '16px', color: 'var(--text-highlight)' }}>{displayEmail}</span>
          </div>
        </div>

        {/* User ID */}
        {profile?.id && (
          <div style={{ marginBottom: '24px' }}>
            <label style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'block', marginBottom: '4px' }}>
              User ID
            </label>
            <span style={{ fontSize: '13px', color: 'var(--text-muted)', fontFamily: 'monospace' }}>{profile.id}</span>
          </div>
        )}

        {/* Member since */}
        {profile?.created_at && (
          <div style={{ marginBottom: '24px' }}>
            <label style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'block', marginBottom: '4px' }}>
              Member Since
            </label>
            <span style={{ fontSize: '14px', color: 'var(--text-highlight)' }}>
              {new Date(profile.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
            </span>
          </div>
        )}

        {/* Logout Button */}
        <button
          onClick={handleLogout}
          className="btn btn-secondary"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            width: 'auto',
            padding: '10px 20px',
          }}
          aria-label="Sign out"
        >
          <LogOut size={16} aria-hidden="true" />
          Sign Out
        </button>
      </div>

      {/* Quick Links */}
      <div className="card" style={{ padding: '24px' }}>
        <h2 style={{ fontSize: '16px', marginBottom: '16px' }}>Quick Links</h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <a
            href="/reports"
            style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              padding: '10px 14px', borderRadius: '8px',
              background: 'var(--bg)', color: 'var(--text-highlight)',
              textDecoration: 'none', fontSize: '14px',
              border: '1px solid var(--border)',
            }}
          >
            <FileText size={16} aria-hidden="true" />
            My Reports
          </a>
        </div>
      </div>
    </div>
  );
}
