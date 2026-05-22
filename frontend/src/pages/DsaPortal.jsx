import { useState, useEffect, useCallback } from 'react';
import { UploadCloud, TrendingUp, Users, CheckCircle2, DollarSign, Copy, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8005/api';

export default function DsaPortal({ t, planKey, getHealthColors }) {
  const { user } = useAuth();
  const [dsaReferrals, setDsaReferrals] = useState(15);
  const [dsaConversionRate, setDsaConversionRate] = useState(40);
  const [copiedRef, setCopiedRef] = useState(false);
  const [dsaLeads, setDsaLeads] = useState([]);
  const [stats, setStats] = useState({ total_leads: 0, conversions: 0, total_commission: 0 });
  const [referralLink, setReferralLink] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const getToken = () => localStorage.getItem('access_token') || '';

  const fetchDsaData = useCallback(async () => {
    if (!user) { setLoading(false); return; }
    setLoading(true);
    setError(null);
    try {
      const headers = { 'Authorization': `Bearer ${getToken()}` };
      const [statsRes, leadsRes, refRes] = await Promise.all([
        fetch(`${API_BASE}/dsa/stats`, { headers }),
        fetch(`${API_BASE}/dsa/leads`, { headers }),
        fetch(`${API_BASE}/dsa/referral-link`, { headers }),
      ]);
      if (statsRes.ok) setStats(await statsRes.json());
      if (leadsRes.ok) setDsaLeads(await leadsRes.json());
      if (refRes.ok) {
        const ref = await refRes.json();
        setReferralLink(ref.referral_link || '');
      }
    } catch (err) {
      setError('Failed to load DSA data');
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => { fetchDsaData(); }, [fetchDsaData]);

  const handleCopyReferralLink = () => {
    navigator.clipboard.writeText(referralLink || 'https://clyr.in/ref/dsa_shiva');
    setCopiedRef(true);
    setTimeout(() => setCopiedRef(false), 2000);
  };

  const handleBulkFileChange = async (e) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const files = Array.from(e.target.files);
    const newLeads = files.map((file) => {
      const randomScore = Math.floor(Math.random() * (850 - 550) + 550);
      const plans = ['Starter', 'Follow-up', 'Recovery'];
      const randomPlan = plans[Math.floor(Math.random() * plans.length)];
      const displayName = file.name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' ');
      return {
        name: displayName.charAt(0).toUpperCase() + displayName.slice(1),
        score: randomScore,
        date: new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }),
        plan: randomPlan,
        status: 'Actioned',
        commission: 100,
      };
    });
    setDsaLeads(prev => [...newLeads, ...prev]);
    try {
      await fetch(`${API_BASE}/dsa/leads`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${getToken()}` },
        body: JSON.stringify(newLeads),
      });
    } catch { /* silent fail */ }
  };

  if (!user) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 20px' }}>
        <h2 style={{ fontSize: '20px', marginBottom: '8px' }}>Sign in required</h2>
        <p style={{ color: 'var(--text-muted)' }}>Please sign in to access the DSA portal.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '60px 0' }}>
        <Loader2 size={32} style={{ animation: 'spin 1s linear infinite', color: 'var(--primary)' }} />
      </div>
    );
  }

  return (
    <div className="dsa-dashboard" role="main" aria-label={t('dsaPortal')}>
      <div className="hero-section" style={{ paddingBottom: '0', marginBottom: '24px' }}>
        <div className="hero-tag" style={{ background: 'var(--primary-glow)', color: 'var(--primary-hover)' }} aria-hidden="true">
          <TrendingUp size={14} /> {t('dsaPortal')}
        </div>
        <h2 className="hero-title" style={{ fontSize: '32px' }}>{t('dsaSubtitle')}</h2>
        <p className="hero-subtitle" style={{ fontSize: '15px' }}>{t('dsaDescription')}</p>
      </div>

      <div className="dsa-stats-grid" role="group" aria-label="Statistics overview">
        <div className="dsa-stat-card" role="status" aria-label={`${stats.total_leads} total leads`}>
          <div className="dsa-stat-icon-box" aria-hidden="true"><Users size={24} /></div>
          <div className="dsa-stat-details">
            <span className="dsa-stat-label">{t('totalLeads')}</span>
            <span className="dsa-stat-value">{stats.total_leads} {t('clients')}</span>
          </div>
        </div>
        <div className="dsa-stat-card" role="status" aria-label={`${stats.conversions} conversions`}>
          <div className="dsa-stat-icon-box green-theme" aria-hidden="true"><CheckCircle2 size={24} /></div>
          <div className="dsa-stat-details">
            <span className="dsa-stat-label">{t('conversions')}</span>
            <span className="dsa-stat-value">{stats.conversions} {t('clients')}</span>
          </div>
        </div>
        <div className="dsa-stat-card" role="status" aria-label={`₹${stats.total_commission} total commission`}>
          <div className="dsa-stat-icon-box yellow-theme" aria-hidden="true"><DollarSign size={24} /></div>
          <div className="dsa-stat-details">
            <span className="dsa-stat-label">{t('totalCommission')}</span>
            <span className="dsa-stat-value">₹{stats.total_commission}</span>
          </div>
        </div>
      </div>

      <div className="dsa-main-grid">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="card" role="region" aria-labelledby="ref-link-heading">
            <h4 id="ref-link-heading" style={{ fontSize: '15px', color: 'var(--text-highlight)', marginBottom: '8px' }}>{t('partnerRefLink')}</h4>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '16px' }}>{t('partnerRefDesc')}</p>
            <div className="dsa-referral-box">
              <div className="dsa-ref-input-group">
                <input type="text" readOnly value={referralLink || 'https://clyr.in/ref/dsa_shiva'} className="dsa-ref-input" aria-label="Referral link" />
                <button className="btn btn-primary" style={{ width: 'auto', padding: '10px 16px' }} onClick={handleCopyReferralLink} aria-label={copiedRef ? t('copied') : t('copy')}>
                  {copiedRef ? t('copied') : t('copy')}
                </button>
              </div>
            </div>
          </div>

          <div className="card" role="region" aria-labelledby="payout-est-heading">
            <h4 id="payout-est-heading" style={{ fontSize: '15px', color: 'var(--text-highlight)', marginBottom: '16px' }}>{t('payoutEstimator')}</h4>
            <div className="dsa-calc-row">
              <div className="sim-input-label-row">
                <label htmlFor="dsa-referrals" className="sim-input-label">{t('expectedReferrals')}</label>
                <span className="sim-input-value" aria-live="polite">{dsaReferrals}</span>
              </div>
              <input id="dsa-referrals" type="range" min="1" max="100" value={dsaReferrals} onChange={(e) => setDsaReferrals(parseInt(e.target.value))} className="simulator-slider" aria-valuemin={1} aria-valuemax={100} aria-valuenow={dsaReferrals} />
            </div>
            <div className="dsa-calc-row" style={{ marginTop: '16px' }}>
              <div className="sim-input-label-row">
                <label htmlFor="dsa-conversion" className="sim-input-label">{t('estConversionRate')}</label>
                <span className="sim-input-value" aria-live="polite">{dsaConversionRate}%</span>
              </div>
              <input id="dsa-conversion" type="range" min="1" max="100" value={dsaConversionRate} onChange={(e) => setDsaConversionRate(parseInt(e.target.value))} className="simulator-slider" aria-valuemin={1} aria-valuemax={100} aria-valuenow={dsaConversionRate} />
            </div>
            <div className="dsa-payout-box" role="status" aria-label={`Projected commission: ₹${Math.round(dsaReferrals * (dsaConversionRate / 100) * 100)}`}>
              <span className="dsa-stat-label" style={{ display: 'block', marginBottom: '4px' }}>{t('projectedCommission')}</span>
              <span className="dsa-payout-val">₹{Math.round(dsaReferrals * (dsaConversionRate / 100) * 100)}</span>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="card" role="region" aria-labelledby="bulk-upload-heading">
            <h4 id="bulk-upload-heading" style={{ fontSize: '15px', color: 'var(--text-highlight)', marginBottom: '8px' }}>{t('bulkUploaderTitle')}</h4>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '16px' }}>{t('bulkUploaderDesc')}</p>
            <div className="upload-zone" onClick={() => document.getElementById('bulk-pdf-upload').click()} style={{ padding: '24px 16px', minHeight: '120px' }} role="button" tabIndex={0} aria-label="Bulk upload credit report PDFs" onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') document.getElementById('bulk-pdf-upload').click(); }}>
              <input type="file" id="bulk-pdf-upload" className="file-input" accept=".pdf" multiple onChange={handleBulkFileChange} aria-label="Choose PDF files for bulk upload" />
              <UploadCloud size={32} className="upload-icon" strokeWidth={1.5} style={{ marginBottom: '8px' }} aria-hidden="true" />
              <p className="upload-title" style={{ fontSize: '13px' }}>{t('bulkUploaderDragDrop')}</p>
            </div>
          </div>

          <div className="card" style={{ padding: '24px 16px' }} role="region" aria-labelledby="client-tracker-heading">
            <h4 id="client-tracker-heading" style={{ fontSize: '15px', color: 'var(--text-highlight)', marginBottom: '16px' }}>{t('clientTracker')}</h4>
            <div className="dsa-table-wrapper" role="region" aria-label="Client leads table" tabIndex={0}>
              <table className="dsa-table">
                <thead>
                  <tr>
                    <th scope="col">{t('colClientName')}</th>
                    <th scope="col">{t('colBureauScore')}</th>
                    <th scope="col">{t('colUploadDate')}</th>
                    <th scope="col">{t('colPlan')}</th>
                    <th scope="col">{t('colStatus')}</th>
                    <th scope="col">{t('colCommission')}</th>
                  </tr>
                </thead>
                <tbody>
                  {dsaLeads.length === 0 ? (
                    <tr><td colSpan={6} style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>No leads yet. Upload reports to get started.</td></tr>
                  ) : dsaLeads.map((lead, idx) => (
                    <tr key={idx}>
                      <td style={{ fontWeight: '500', color: 'var(--text-highlight)' }}>{lead.name}</td>
                      <td><span className={`health-badge ${getHealthColors(lead.score).class}`} style={{ padding: '2px 8px', fontSize: '11px', display: 'inline-block' }} aria-label={`Score: ${lead.score}`}>{lead.score}</span></td>
                      <td>{lead.date}</td>
                      <td>{t(planKey(lead.plan))}</td>
                      <td><span className={`status-badge ${lead.status === 'Paid' ? 'ready' : 'actioned'}`} aria-label={`Status: ${lead.status}`}>{lead.status === 'Paid' ? t('statusDispatched') : t('statusRoadmap')}</span></td>
                      <td style={{ fontWeight: '600', color: lead.status === 'Paid' ? 'var(--color-green)' : 'var(--text-muted)' }}>₹{lead.commission}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
