import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiFetch } from '../api/client';
import LoadingSpinner from '../components/LoadingSpinner';
import { Eye, Download, FileText, AlertCircle } from 'lucide-react';

function StatusBadge({ status }) {
  const s = (status || '').toLowerCase();
  let cls = 'status-default';
  if (s.includes('complete') || s.includes('done') || s.includes('success')) cls = 'status-green';
  else if (s.includes('progress') || s.includes('pending') || s.includes('processing')) cls = 'status-yellow';
  else if (s.includes('fail') || s.includes('error')) cls = 'status-red';
  return <span className={`report-status-badge ${cls}`}>{status || 'Unknown'}</span>;
}

function ScoreDisplay({ score }) {
  const s = Number(score) || 0;
  let color = 'var(--color-red)';
  if (s >= 750) color = 'var(--color-green)';
  else if (s >= 650) color = 'var(--color-yellow)';
  return <span className="report-score" style={{ color }}>{s}</span>;
}

export default function ReportsPage({ t, setCurrentView, setReportData }) {
  const { user } = useAuth();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [downloadingId, setDownloadingId] = useState(null);

  const fetchReports = useCallback(async () => {
    if (!user) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch('/reports');
      setReports(Array.isArray(data) ? data : (data.reports || []));
    } catch (err) {
      console.error('Failed to fetch reports:', err);
      setError(err.message || 'Failed to load reports');
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  const handleView = useCallback((report) => {
    setReportData(report);
    setCurrentView('dashboard');
  }, [setReportData, setCurrentView]);

  const handleDownload = useCallback(async (report, reportId) => {
    setDownloadingId(reportId);
    try {
      const blob = await apiFetch('/download', {
        method: 'POST',
        body: JSON.stringify({ ...report }),
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const name = (report.customer_name || 'report').replace(/\s+/g, '_');
      link.setAttribute('download', `CLYR_Report_${name}.pdf`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download failed:', err);
      setError('Failed to download PDF. Please try again.');
    } finally {
      setDownloadingId(null);
    }
  }, []);

  const formatDate = (dateStr) => {
    if (!dateStr) return '—';
    try {
      return new Date(dateStr).toLocaleDateString(undefined, {
        year: 'numeric', month: 'short', day: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  if (!user) {
    return (
      <div className="reports-empty" role="status">
        <AlertCircle size={48} style={{ color: 'var(--text-muted)', marginBottom: '16px' }} />
        <h2 style={{ fontSize: '20px', marginBottom: '8px' }}>Sign in required</h2>
        <p style={{ color: 'var(--text-muted)' }}>Please sign in to view your report history.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '60px 0' }}>
        <LoadingSpinner text="Loading reports..." subtext="" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="reports-empty" role="alert">
        <AlertCircle size={48} style={{ color: 'var(--color-red)', marginBottom: '16px' }} />
        <h2 style={{ fontSize: '20px', marginBottom: '8px' }}>Error loading reports</h2>
        <p style={{ color: 'var(--text-muted)', marginBottom: '16px' }}>{error}</p>
        <button className="btn btn-secondary" onClick={fetchReports}>Retry</button>
      </div>
    );
  }

  if (reports.length === 0) {
    return (
      <div className="reports-empty" role="status">
        <FileText size={48} style={{ color: 'var(--text-muted)', marginBottom: '16px' }} />
        <h2 style={{ fontSize: '20px', marginBottom: '8px' }}>No reports yet</h2>
        <p style={{ color: 'var(--text-muted)', marginBottom: '24px' }}>
          Upload your first credit report to get started.
        </p>
        <button className="btn btn-primary" onClick={() => setCurrentView('uploader')}>
          Upload Report
        </button>
      </div>
    );
  }

  return (
    <div className="reports-container">
      <div className="reports-header">
        <h2 className="reports-title">My Reports</h2>
        <span className="reports-count">{reports.length} report{reports.length !== 1 ? 's' : ''}</span>
      </div>

      <div className="reports-table-wrapper" role="region" aria-label="Report history table">
        <table className="reports-table">
          <thead>
            <tr>
              <th scope="col">Customer</th>
              <th scope="col">Score</th>
              <th scope="col">Date</th>
              <th scope="col">Status</th>
              <th scope="col" style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {reports.map((report, idx) => {
              const id = report.id || idx;
              const isDownloading = downloadingId === id;
              return (
                <tr key={id} className="report-row">
                  <td className="report-customer">
                    <FileText size={16} aria-hidden="true" style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
                    <span className="report-customer-name">{report.customer_name || '—'}</span>
                  </td>
                  <td><ScoreDisplay score={report.score} /></td>
                  <td className="report-date">{formatDate(report.created_at || report.date)}</td>
                  <td><StatusBadge status={report.status} /></td>
                  <td className="report-actions">
                    <button
                      className="btn btn-secondary btn-sm report-btn-view"
                      onClick={() => handleView(report)}
                      aria-label={`View report for ${report.customer_name || 'customer'}`}
                    >
                      <Eye size={14} aria-hidden="true" /> View
                    </button>
                    <button
                      className="btn btn-secondary btn-sm report-btn-download"
                      onClick={() => handleDownload(report, id)}
                      disabled={isDownloading}
                      aria-busy={isDownloading}
                      aria-label={`Download PDF for ${report.customer_name || 'customer'}`}
                    >
                      {isDownloading ? (
                        <><span className="spinner spinner-sm" aria-hidden="true" /> ...</>
                      ) : (
                        <><Download size={14} aria-hidden="true" /> PDF</>
                      )}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
