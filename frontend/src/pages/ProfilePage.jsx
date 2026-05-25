import { useAuth } from '../context/AuthContext';
import { User, Mail, LogOut } from 'lucide-react';

export default function ProfilePage() {
  const { user, signOut } = useAuth();

  const displayName = user?.full_name || user?.email?.split('@')[0] || 'User';
  const displayEmail = user?.email || '';
  const displayRole = user?.role || null;

  const formattedJoin = user?.created_at
    ? new Date(user.created_at).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    : null;

  const handleSignOut = async () => {
    await signOut();
  };

  return (
    <div style={{ maxWidth: '520px', margin: '48px auto 0', padding: '0 20px' }}>
      <h1 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '24px' }}>
        My Profile
      </h1>

      <div className="card" style={{ padding: '32px' }}>
        {/* Avatar */}
        <div
          style={{
            width: '68px',
            height: '68px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, var(--primary), var(--primary-hover))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '24px',
          }}
        >
          <User size={30} color="#fff" aria-hidden="true" />
        </div>

        {/* Full Name */}
        <div style={{ marginBottom: '18px' }}>
          <label
            style={{
              fontSize: '11px',
              fontWeight: 600,
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.6px',
              display: 'block',
              marginBottom: '6px',
            }}
          >
            Full Name
          </label>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <User size={15} color="var(--text-muted)" aria-hidden="true" />
            <span style={{ fontSize: '16px', color: 'var(--text-highlight)' }}>
              {displayName}
            </span>
          </div>
        </div>

        {/* Email */}
        <div style={{ marginBottom: '18px' }}>
          <label
            style={{
              fontSize: '11px',
              fontWeight: 600,
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.6px',
              display: 'block',
              marginBottom: '6px',
            }}
          >
            Email
          </label>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Mail size={15} color="var(--text-muted)" aria-hidden="true" />
            <span style={{ fontSize: '16px', color: 'var(--text-highlight)' }}>
              {displayEmail}
            </span>
          </div>
        </div>

        {/* Role */}
        {displayRole && (
          <div style={{ marginBottom: '28px' }}>
            <label
              style={{
                fontSize: '11px',
                fontWeight: 600,
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.6px',
                display: 'block',
                marginBottom: '6px',
              }}
            >
              Role
            </label>
            <span
              style={{
                display: 'inline-block',
                fontSize: '13px',
                fontWeight: 600,
                color: 'var(--primary)',
                background: 'var(--primary-glow, rgba(99,102,241,0.12))',
                padding: '4px 12px',
                borderRadius: '9999px',
                textTransform: 'capitalize',
              }}
            >
              {displayRole}
            </span>
          </div>
        )}

        {/* Member Since */}
        {!displayRole && <div style={{ marginBottom: '28px' }}></div>}
        {formattedJoin && (
          <div style={{ marginBottom: '28px' }}>
            <label
              style={{
                fontSize: '11px',
                fontWeight: 600,
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.6px',
                display: 'block',
                marginBottom: '6px',
              }}
            >
              Member Since
            </label>
            <span style={{ fontSize: '14px', color: 'var(--text-highlight)' }}>
              {formattedJoin}
            </span>
          </div>
        )}

        {/* Sign Out */}
        <button
          onClick={handleSignOut}
          className="btn btn-secondary"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '10px 22px',
          }}
          aria-label="Sign out"
        >
          <LogOut size={16} aria-hidden="true" />
          Sign Out
        </button>
      </div>
    </div>
  );
}
