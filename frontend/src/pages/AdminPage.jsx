/**
 * CLYR v2 — Admin Dashboard
 * Only accessible to users with role='admin'.
 */
import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiFetch } from '../api/client';
import LoadingSpinner from '../components/LoadingSpinner';
import { Users, FileText, IndianRupee, Mail, AlertCircle } from 'lucide-react';

export default function AdminPage({ t }) {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (user?.role !== 'admin') {
      setError('Access denied. Admin only.');
      setLoading(false);
      return;
    }
    apiFetch('/admin/dashboard')
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [user]);

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', padding: '60px' }}><LoadingSpinner text="Loading..." subtext="" /></div>;
  if (error) return <div className="error-banner" role="alert" style={{ margin: '24px auto', maxWidth: '680px' }}><AlertCircle size={16} /> {error}</div>;
  if (!data) return null;

  const stats = [
    { icon: Users, label: 'Total Users', value: data.total_users || 0, color: 'var(--primary)' },
    { icon: FileText, label: 'Reports Generated', value: data.total_reports || 0, color: 'var(--color-green)' },
    { icon: IndianRupee, label: 'Revenue (₹)', value: ((data.total_revenue || 0) / 100).toLocaleString('en-IN'), color: 'var(--color-yellow)' },
    { icon: Mail, label: 'Waitlist', value: data.total_waitlist || 0, color: 'var(--accent)' },
  ];

  return (
    <div style={{ maxWidth: '1080px', margin: '0 auto', padding: '32px 24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 800, marginBottom: '8px' }}>Admin Dashboard</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: '32px' }}>CLYR platform overview</p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '40px' }}>
        {stats.map((stat, i) => (
          <div key={i} className="card" style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '20px' }}>
            <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: `${stat.color}20`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: stat.color }}>
              <stat.icon size={24} />
            </div>
            <div>
              <div style={{ fontSize: '24px', fontWeight: 700 }}>{stat.value}</div>
              <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{stat.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Signups */}
      <div className="card" style={{ padding: '24px', marginBottom: '24px' }}>
        <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '16px' }}>Recent Signups</h2>
        {data.recent_signups?.length > 0 ? (
          <table className="reports-table">
            <thead><tr><th>Email</th><th>Name</th><th>Date</th></tr></thead>
            <tbody>
              {data.recent_signups.map((u, i) => (
                <tr key={i}><td>{u.email}</td><td>{u.full_name || '—'}</td><td>{new Date(u.created_at).toLocaleDateString()}</td></tr>
              ))}
            </tbody>
          </table>
        ) : <p style={{ color: 'var(--text-muted)' }}>No recent signups.</p>}
      </div>

      {/* Recent Orders */}
      <div className="card" style={{ padding: '24px' }}>
        <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '16px' }}>Recent Orders</h2>
        {data.recent_orders?.length > 0 ? (
          <table className="reports-table">
            <thead><tr><th>Plan</th><th>Amount</th><th>Status</th><th>Date</th></tr></thead>
            <tbody>
              {data.recent_orders.map((o, i) => (
                <tr key={i}><td>{o.plan}</td><td>₹{(o.amount / 100).toLocaleString('en-IN')}</td><td>{o.status}</td><td>{new Date(o.created_at).toLocaleDateString()}</td></tr>
              ))}
            </tbody>
          </table>
        ) : <p style={{ color: 'var(--text-muted)' }}>No orders yet.</p>}
      </div>
    </div>
  );
}
