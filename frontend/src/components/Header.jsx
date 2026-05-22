import { Sparkles, RefreshCw, Globe, LogIn, LogOut, User } from 'lucide-react';
import { LANGUAGES } from '../i18n/translations';
import { useState } from 'react';
import AuthModal from './AuthModal';

export default function Header({ lang, setLang, t, currentView, setCurrentView, reportData, handleReset, user, signOut }) {
  const [showAuth, setShowAuth] = useState(false);

  return (
    <>
      {showAuth && <AuthModal onClose={() => setShowAuth(false)} />}
      <header className="app-header" role="banner">
        <div
          className="brand"
          onClick={() => setCurrentView('landing')}
          style={{ cursor: 'pointer' }}
          role="button"
          tabIndex={0}
          aria-label={`${t('brand')} - ${t('home')}`}
          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setCurrentView('landing'); }}
        >
          <div className="brand-logo" aria-hidden="true">
            <Sparkles size={28} strokeWidth={2.5} />
          </div>
          <h1 className="brand-name">{t('brand')}</h1>
          <span className="badge-demo" aria-label="Beta version">{t('beta')}</span>
        </div>

        <nav className="nav-menu" role="navigation" aria-label="Main navigation">
          <button
            className={`nav-item ${currentView === 'landing' ? 'active' : ''}`}
            onClick={() => setCurrentView('landing')}
            aria-current={currentView === 'landing' ? 'page' : undefined}
          >
            {t('home')}
          </button>
          <button
            className={`nav-item ${(currentView === 'uploader' || currentView === 'dashboard') ? 'active' : ''}`}
            onClick={() => {
              if (reportData) setCurrentView('dashboard');
              else setCurrentView('uploader');
            }}
            aria-current={(currentView === 'uploader' || currentView === 'dashboard') ? 'page' : undefined}
          >
            {reportData ? t('analysisDashboard') : t('uploadReport')}
          </button>
          <button
            className={`nav-item ${currentView === 'dsa' ? 'active' : ''}`}
            onClick={() => setCurrentView('dsa')}
            aria-current={currentView === 'dsa' ? 'page' : undefined}
          >
            {t('dsaPortal')}
          </button>
          {user && (
            <button
              className={`nav-item ${currentView === 'reports' ? 'active' : ''}`}
              onClick={() => setCurrentView('reports')}
              aria-current={currentView === 'reports' ? 'page' : undefined}
            >
              {t('myReports')}
            </button>
          )}
        </nav>

        <div className="header-actions">
          <div className="lang-selector" role="group" aria-label="Language selection">
            <Globe size={15} aria-hidden="true" />
            <select
              value={lang}
              onChange={(e) => setLang(e.target.value)}
              aria-label="Select language"
            >
              {LANGUAGES.map(l => (
                <option key={l.code} value={l.code}>{l.nativeLabel}</option>
              ))}
            </select>
          </div>
          {reportData && (
            <button
              className="btn btn-secondary"
              style={{ width: 'auto', padding: '8px 16px', fontSize: '13px' }}
              onClick={handleReset}
              aria-label={t('resetApp')}
            >
              <RefreshCw size={14} aria-hidden="true" /> {t('resetApp')}
            </button>
          )}
          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '13px', color: 'var(--text-muted)', maxWidth: '120px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {user.email}
              </span>
              <button
                className="btn btn-secondary"
                style={{ width: 'auto', padding: '8px 14px', fontSize: '13px' }}
                onClick={signOut}
                aria-label="Sign out"
              >
                <LogOut size={14} aria-hidden="true" /> Sign Out
              </button>
            </div>
          ) : (
            <button
              className="btn btn-primary"
              style={{ width: 'auto', padding: '8px 16px', fontSize: '13px' }}
              onClick={() => setShowAuth(true)}
              aria-label="Sign in"
            >
              <LogIn size={14} aria-hidden="true" /> Sign In
            </button>
          )}
        </div>
      </header>
    </>
  );
}
