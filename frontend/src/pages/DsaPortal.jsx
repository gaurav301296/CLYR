/**
 * CLYR v2 — DSA Partner Portal
 * For DSAs to track clients, commissions, and referral links.
 */
import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiFetch } from '../api/client';
import LoadingSpinner from '../components/LoadingSpinner';
import { Users, DollarSign, TrendingUp, Copy, CheckCircle2, AlertCircle } from 'lucide-react';

export default function DsaPortal({ t, planKey, getHealthColors }) {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [leads, setLeads] = useState([]);
  const [referral, setReferral] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!user) { setLoading(false); return; }
    Promise.all([
      apiFetch('/dsa/stats'),
      apiFetch('/dsa/leads'),
      apiFetch('/dsa/referral-link'),
    ])
      .then(([s, l, r]) => { setStats(s); setLeads(l); setReferral(r); })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [user]);

  const copyLink = () => {
    if (referral?.referral_link) {
      navigator.clipboard.writeText(referral.referral_link);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!user) return <div className="error-banner" role="alert" style={{ margin: '24px auto', maxWidth: '680px' }}>Sign in required.</div>;
  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', padding: '60px' }}><LoadingSpinner text="Loading..." subtext="" /></div>;
  if (error) return <div className="error-banner" role="alert" style={{ margin: '24px auto', maxWidth: '680px' }}><AlertCircle size={16} /> {error}</div>;

  return (
    <div style={{ maxWidth: '1080px', margin: '0 auto', padding: '32px 24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 800, marginBottom: '8px' }}>Partner Portal</h1>
      <p style={{ color: 'var(--text-muted)', marginBottom: '32px' }}>Client lao, commission kamao. Simple.</p>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '32px' }}>
        <div className="card" style={{ padding: '20px', textAlign: 'center' }}>
          <Users size={24} style={{ color: 'var(--primary)', margin: '0 auto 8px' }} />
          <div style={{ fontSize: '24px', fontWeight: 700 }}>{stats?.total_leads || 0}</div>
          <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Total Leads</div>
        </div>
        <div className="card" style={{ padding: '20px', textAlign: 'center' }}>
          <TrendingUp size={24} style={{ color: 'var(--color-green)', margin: '0 auto 8px' }} />
          <div style={{ fontSize: '24px', fontWeight: 700 }}>{stats?.conversions || 0}</div>
          <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Conversions</div>
        </div>
        <div className="card" style={{ padding: '20px', textAlign: 'center' }}>
          <DollarSign size={24} style={{ color: 'var(--color-yellow)', margin: '0 auto 8px' }} />
          <div style={{ fontSize: '24px', fontWeight: 700 }}>₹{(stats?.total_commission || 0).toLocaleString('en-IN')}</div>
          <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Total Commission</div>
        </div>
      </div>

      {/* Referral Link */}
      {referral && (
        <div className="card" style={{ padding: '24px', marginBottom: '32px' }}>
          <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '12px' }}>Tera Partner Referral Link</h2>
          <p style={{ fontSize: '14px', color: 'var(--text-muted)', marginBottom: '16px' }}>
            Is link ko clients ko bhejo. Unki har report pe tera commission — automatic.
          </p>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <input
              type="text"
              value={referral.referral_link}
              readOnly
              style={{ flex: 1, padding: '12px 16px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg)', color: 'var(--text-highlight)', fontSize: '14px' }}
            />
            <button className="btn btn-primary" onClick={copyLink}>
              {copied ? <><CheckCircle2 size={16} /> Copied!</> : <><Copy size={16} /> Copy</>}
            </button>
          </div>
        </div>
      )}

      {/* Leads Table */}
      <div className="card" style={{ padding: '24px' }}>
        <h2 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '16px' }}>Client Leads</h2>
        {leads.length > 0 ? (
          <table className="reports-table">
            <thead><tr><th>Name</th><th>Score</th><th>Plan</th><th>Status</th><th>Commission</th></tr></thead>
            <tbody>
              {leads.map((lead, i) => (
                <tr key={i}>
                  <td>{lead.name || '—'}</td>
                  <td>{lead.score || '—'}</td>
                  <td>{lead.plan}</td>
                  <td>{lead.status}</td>
                  <td>₹{(lead.commission || 0).toLocaleString('en-IN')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p style={{ color: 'var(--text-muted)' }}>Abhi koi leads nahi hain. Referral link share karo!</p>
        )}
      </div>
    </div>
  );
}
