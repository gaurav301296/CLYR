/**
 * CLYR v2 — Dashboard Page
 * Shows analysis results: score gauge, issues, action checklist, timeline, simulator.
 * World-class data visualization for credit health.
 */
import { AlertTriangle, CheckCircle2, Calendar, Download, RefreshCw } from 'lucide-react';

function ScoreGauge({ score, health, t, handleDownloadPDF, downloading, reportData }) {
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (health.percent / 100) * circumference;

  return (
    <div className="card score-card" role="region" aria-label={t('scoreSummary') || 'Score Summary'}>
      <h3 style={{ fontSize: '16px', color: 'var(--text-muted)', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {t('scoreSummary') || 'Tera CIBIL Score'}
      </h3>
      <div className="score-gauge-container" role="img" aria-label={`Credit score: ${score} out of 900. Status: ${health.name}.`}>
        <svg width="180" height="180" viewBox="0 0 180 180" style={{ transform: 'rotate(-90deg)' }} aria-hidden="true">
          <circle cx="90" cy="90" r={radius} fill="transparent" stroke="var(--border)" strokeWidth="10" />
          <circle cx="90" cy="90" r={radius} fill="transparent" stroke={health.stroke} strokeWidth="10"
            strokeDasharray={circumference} strokeDashoffset={strokeDashoffset} strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 1.5s ease-out' }} />
        </svg>
        <div className="score-number">
          <span className="score-value">{score}</span>
          <span className="score-label">{t('score') || 'Score'}</span>
        </div>
      </div>
      <div className={`health-badge ${health.class}`} aria-label={`Credit health: ${health.name}`}>{health.name}</div>
      <ul className="client-meta-list" aria-label="Client information">
        <li className="client-meta-item">
          <span className="client-meta-label">{t('customerName') || 'Naam'}</span>
          <span className="client-meta-value">{reportData?.customer_name || '—'}</span>
        </li>
        <li className="client-meta-item">
          <span className="client-meta-label">{t('bureauHealth') || 'Credit Health'}</span>
          <span className="client-meta-value">{reportData?.general_health || '—'}</span>
        </li>
      </ul>
    </div>
  );
}

function SimulatorCard({ t, reportData, simulatorResolutions, setSimulatorResolutions, utilizationSlider, setUtilizationSlider, simulatedScore, simulatedScoreDelta }) {
  return (
    <div className="simulator-card" role="region" aria-labelledby="sim-title">
      <h4 id="sim-title" style={{ fontSize: '16px', color: 'var(--text-highlight)', fontWeight: '600', marginBottom: '4px' }}>
        {t('simTitle') || 'Score Simulator — Kya Hoga Agar...'}
      </h4>
      <p style={{ fontSize: '12.5px', color: 'var(--text-muted)', marginBottom: '20px' }}>
        {t('simSubtitle') || 'Defaults clear karoge toh score kitna badhega? Slide karke dekho.'}
      </p>
      <div className="simulator-grid">
        <div className="simulator-gauge" role="img" aria-label={`Estimated future score: ${simulatedScore}.`}>
          <div className={`sim-score-wrapper ${simulatedScoreDelta > 0 ? 'boosted' : ''}`}>
            <span className="sim-score-value">{simulatedScore}</span>
            <span className="sim-score-label">{t('estScore') || 'Est. Score'}</span>
          </div>
          {simulatedScoreDelta > 0 ? (
            <span className="score-delta-badge">+{simulatedScoreDelta} {t('boost') || 'Boost!'}</span>
          ) : simulatedScoreDelta < 0 ? (
            <span className="score-delta-badge neutral" style={{ backgroundColor: 'var(--color-red-bg)', color: 'var(--color-red)', borderColor: 'rgba(239, 68, 68, 0.2)' }}>
              {simulatedScoreDelta} {t('drop') || 'Drop'}
            </span>
          ) : (
            <span className="score-delta-badge neutral">{t('noChange') || 'No change'}</span>
          )}
        </div>
        <div className="simulator-details">
          <div className="sim-input-section">
            <div className="sim-input-label-row">
              <label htmlFor="utilization-slider" className="sim-input-label">{t('simUtilization') || 'Credit Card Utilization'}</label>
              <span className="sim-input-value" aria-live="polite">{utilizationSlider}%</span>
            </div>
            <input
              id="utilization-slider"
              type="range" min="0" max="100"
              value={utilizationSlider}
              onChange={(e) => setUtilizationSlider(parseInt(e.target.value))}
              className="simulator-slider"
              aria-valuemin={0} aria-valuemax={100} aria-valuenow={utilizationSlider}
              aria-valuetext={`${utilizationSlider}% credit utilization`}
            />
            <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: '4px 0 0' }}>
              {t('simUtilizationHint') || 'Kam utilization = healthy score. Golden rule: 30% se rakho.'}
            </p>
          </div>
          <fieldset className="sim-input-section" style={{ border: 'none', padding: 0, margin: 0 }}>
            <legend className="sim-input-label">{t('simResolveOverdue') || 'Clear Karo Overdues'}</legend>
            <div className="sim-checkbox-list" style={{ marginTop: '8px' }} role="group" aria-label="Simulate resolving overdue accounts">
              {(reportData?.issues || []).map((issue, idx) => {
                const isChecked = simulatorResolutions.has(idx);
                const points = ['critical', 'red', 'major'].includes((issue.type || '').toLowerCase()) ? 45 : 25;
                return (
                  <div
                    key={idx}
                    className={`sim-checkbox-item ${isChecked ? 'checked' : ''}`}
                    role="checkbox"
                    aria-checked={isChecked}
                    tabIndex={0}
                    onClick={() => {
                      const next = new Set(simulatorResolutions);
                      if (next.has(idx)) next.delete(idx); else next.add(idx);
                      setSimulatorResolutions(next);
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        const next = new Set(simulatorResolutions);
                        if (next.has(idx)) next.delete(idx); else next.add(idx);
                        setSimulatorResolutions(next);
                      }
                    }}
                  >
                    <div className="sim-checkbox-check" aria-hidden="true">
                      {isChecked && <div style={{ width: '6px', height: '6px', backgroundColor: 'var(--primary)', borderRadius: '50%' }} />}
                    </div>
                    <span className="sim-checkbox-text">{t('resolveOverdueFor') || 'Iska overdue clear kar doon?'} <strong>{issue.account}</strong></span>
                    <span className="sim-checkbox-points">+{points} pts</span>
                  </div>
                );
              })}
            </div>
          </fieldset>
          <div className="sim-notes" role="note">{t('simDisclaimer') || 'Yeh estimation hai, guarantee nahi.'}</div>
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage({
  t, reportData, getHealthColors, handleDownloadPDF, downloading,
  checkedTasks, handleToggleTask,
  simulatorResolutions, setSimulatorResolutions,
  utilizationSlider, setUtilizationSlider,
  simulatedScore, simulatedScoreDelta
}) {
  if (!reportData) return null;

  const health = getHealthColors(reportData.score);
  const issues = reportData.issues || [];
  const actionSteps = reportData.action_steps || [];
  const timeline = reportData.timeline || [];

  return (
    <div className="results-grid" role="main" aria-label={t('analysisDashboard') || 'Analysis Dashboard'}>
      <div className="panel-sticky">
        <ScoreGauge score={reportData.score} health={health} t={t} handleDownloadPDF={handleDownloadPDF} downloading={downloading} reportData={reportData} />
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <button className="btn btn-primary" onClick={handleDownloadPDF} disabled={downloading} aria-busy={downloading}>
            {downloading ? (
              <><RefreshCw className="spinner" size={16} style={{ margin: 0, width: 16, height: 16 }} aria-hidden="true" /> {t('compilingBtn') || 'PDF bana raha hai...'}</>
            ) : (
              <><Download size={16} aria-hidden="true" /> {t('downloadBtn') || 'PDF Download Karo'}</>
            )}
          </button>
          <p style={{ fontSize: '11px', color: 'var(--text-muted)', textAlign: 'center' }}>
            {t('downloadDesc') || 'Print-ready dispute letters + recovery roadmap.'}
          </p>
        </div>
      </div>

      <div className="content-panel">
        <SimulatorCard t={t} reportData={reportData} simulatorResolutions={simulatorResolutions} setSimulatorResolutions={setSimulatorResolutions} utilizationSlider={utilizationSlider} setUtilizationSlider={setUtilizationSlider} simulatedScore={simulatedScore} simulatedScoreDelta={simulatedScoreDelta} />

        {/* Issues Section */}
        <section aria-labelledby="issues-heading">
          <div className="panel-header">
            <h3 id="issues-heading" className="panel-title">
              <AlertTriangle size={18} className="icon-red" style={{ color: 'var(--color-red)' }} aria-hidden="true" />
              {t('flaggedAccounts') || 'Flagged Accounts'} ({issues.length})
            </h3>
          </div>
          <div className="issue-list" style={{ marginTop: '16px' }} role="list">
            {issues.map((issue, idx) => (
              <div key={idx} className="issue-item" role="listitem">
                <div className={`issue-bar ${['critical', 'red'].includes((issue.type || '').toLowerCase()) ? 'red' : 'yellow'}`} aria-hidden="true" />
                <div className="issue-body">
                  <div className="issue-header">
                    <span className="issue-account">{issue.account}</span>
                    <span className={`issue-badge ${['critical', 'red'].includes((issue.type || '').toLowerCase()) ? 'red' : 'yellow'}`} aria-label={`Severity: ${issue.type}`}>{issue.type}</span>
                  </div>
                  <div className="issue-detail-row">
                    <div className="issue-label">{t('problemSpotted') || 'Problem Kya Hai'}</div>
                    <div className="issue-desc">{issue.details}</div>
                  </div>
                  <div className="issue-detail-row" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                    <div>
                      <div className="issue-label">{t('targetImpact') || 'Score Pe Kya Asar'}</div>
                      <div className="issue-desc" style={{ fontSize: '13.5px', fontWeight: '500' }}>{issue.impact}</div>
                    </div>
                    <div>
                      <div className="issue-label">{t('actionRequired') || 'Kya Karna Padega'}</div>
                      <div className="issue-desc" style={{ fontSize: '13.5px', fontWeight: '500' }}>{issue.action}</div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Action Checklist */}
        <section aria-labelledby="checklist-heading">
          <div className="panel-header">
            <h3 id="checklist-heading" className="panel-title">
              <CheckCircle2 size={18} style={{ color: 'var(--color-green)' }} aria-hidden="true" />
              {t('disputePlan') || 'Dispute Action Plan'}
            </h3>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }} aria-live="polite">
              {checkedTasks.size} {t('of') || '/'} {actionSteps.length} {t('completed') || 'done'}
            </span>
          </div>
          <div className="checklist-container" style={{ marginTop: '16px' }} role="list" aria-label="Dispute action checklist">
            {actionSteps.map((step, idx) => {
              const isChecked = checkedTasks.has(idx);
              return (
                <div
                  key={idx}
                  className={`checklist-item ${isChecked ? 'checked' : ''}`}
                  role="checkbox"
                  aria-checked={isChecked}
                  tabIndex={0}
                  onClick={() => handleToggleTask(idx)}
                  onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleToggleTask(idx); } }}
                >
                  <div className="checkbox-custom" aria-hidden="true">
                    <CheckCircle2 size={16} style={{ strokeWidth: 3 }} />
                  </div>
                  <span className="checklist-text">{step}</span>
                </div>
              );
            })}
          </div>
        </section>

        {/* Timeline */}
        <section aria-labelledby="timeline-heading">
          <div className="panel-header">
            <h3 id="timeline-heading" className="panel-title">
              <Calendar size={18} style={{ color: 'var(--primary)' }} aria-hidden="true" />
              {t('restorationTimeline') || 'Score Recovery ka Timeline'}
            </h3>
          </div>
          <div className="timeline-list" style={{ marginTop: '16px' }} role="list" aria-label="Credit score restoration timeline">
            {timeline.map((item, idx) => {
              let statusClass = 'target';
              if ((item.status || '').toLowerCase().includes('progress')) statusClass = 'in-progress';
              if ((item.status || '').toLowerCase().includes('critical')) statusClass = 'critical';
              return (
                <div key={idx} className="timeline-item active" role="listitem">
                  <div className="timeline-dot" aria-hidden="true" />
                  <div className="timeline-content-card">
                    <div className="timeline-header">
                      <span className="timeline-phase">{item.phase}</span>
                      <span className={`timeline-status ${statusClass}`}>{item.status}</span>
                    </div>
                    <p className="timeline-task">{item.task}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
}
