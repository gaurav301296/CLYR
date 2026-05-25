import { useState, useRef, useEffect } from 'react';
import { RefreshCw, Globe, LogIn, LogOut, User, Menu, X, ChevronDown, FileText, Home, Upload } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { LANGUAGES } from '../config';
import AuthModal from './AuthModal';

const LOGO_PATH = '/logo-clyr.png';

export default function Header({ lang, setLang, t, currentView, setCurrentView, reportData, handleReset }) {
  const { user, signOut } = useAuth();
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const [showAuth, setShowAuth] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setShowUserDropdown(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close mobile menu on view change
  const navigateTo = (view) => {
    setCurrentView(view);
    setShowMobileMenu(false);
    setShowUserDropdown(false);
  };

  const userInitial = user?.email ? user.email.charAt(0).toUpperCase() : '?';
  const userDisplayName = user?.full_name || user?.email?.split('@')[0] || t('home');

  const navItems = [
    { key: 'home', label: t('home'), icon: Home, view: 'landing' },
    { key: 'reports', label: reportData ? t('analysisDashboard') : t('myReports'), icon: FileText, view: reportData ? 'dashboard' : 'reports' },
    { key: 'upload', label: t('uploadReport'), icon: Upload, view: 'uploader' },
  ];

  const isActive = (view) => {
    if (view === 'landing' && currentView === 'landing') return true;
    if (view === 'dashboard' && (currentView === 'dashboard' || currentView === 'uploader')) return true;
    if (view === 'reports' && currentView === 'reports') return true;
    return false;
  };

  return (
    <header className="app-header" role="banner">
      {/* Brand — Left */}
      <div
        className="brand"
        onClick={() => navigateTo('landing')}
        style={{ cursor: 'pointer' }}
        role="button"
        tabIndex={0}
        aria-label={`${t('brand')} - ${t('home')}`}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') navigateTo('landing'); }}
      >
        <div className="brand-logo" aria-hidden="true">
          <img src={LOGO_PATH} alt="" width="38" height="38" />
        </div>
        <h1 className="brand-name">{t('brand')}</h1>
        <span className="badge-demo" aria-label="Beta version">{t('beta')}</span>
      </div>

      {/* Nav Menu — Center (visible on tablet+) */}
      <nav className="nav-menu" role="navigation" aria-label="Main navigation">
        <button
          className={`nav-item ${currentView === 'landing' ? 'active' : ''}`}
          onClick={() => navigateTo('landing')}
          aria-current={currentView === 'landing' ? 'page' : undefined}
        >
          <span className="nav-item-label">
            {t('home')}
          </span>
        </button>
        <button
          className={`nav-item ${(currentView === 'uploader' || currentView === 'dashboard') ? 'active' : ''}`}
          onClick={() => {
            if (reportData) navigateTo('dashboard');
            else navigateTo('uploader');
          }}
          aria-current={(currentView === 'uploader' || currentView === 'dashboard') ? 'page' : undefined}
        >
          <span className="nav-item-label">
            {reportData ? t('analysisDashboard') : t('uploadReport')}
          </span>
        </button>
        {user && (
          <button
            className={`nav-item ${currentView === 'reports' ? 'active' : ''}`}
            onClick={() => navigateTo('reports')}
            aria-current={currentView === 'reports' ? 'page' : undefined}
          >
            <span className="nav-item-label">
              {t('myReports')}
            </span>
          </button>
        )}
      </nav>

      {/* Actions — Right */}
      <div className="header-actions">
        {/* Language Switcher */}
        <div className="lang-selector" role="group" aria-label="Language selection">
          <Globe size={15} aria-hidden="true" />
          <select
            value={lang}
            onChange={(e) => setLang(e.target.value)}
            aria-label="Select language"
          >
            {LANGUAGES.map(l => (
              <option key={l.code} value={l.code}>{l.nativeName}</option>
            ))}
          </select>
        </div>

        {/* Reset button when report loaded */}
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

        {/* User Menu */}
        {user ? (
          <div className="user-menu" ref={dropdownRef} style={{ position: 'relative' }}>
            <button
              className="user-menu-trigger"
              onClick={() => setShowUserDropdown(!showUserDropdown)}
              aria-expanded={showUserDropdown}
              aria-haspopup="true"
              aria-label="User menu"
            >
              <div className="user-avatar">
                {userInitial}
              </div>
              <span className="user-email-text">
                {userDisplayName}
              </span>
              <ChevronDown size={14} className={`chevron ${showUserDropdown ? 'open' : ''}`} />
            </button>

            {showUserDropdown && (
              <div className="user-dropdown" role="menu">
                <div className="user-dropdown-header">
                  <div className="user-avatar-lg">{userInitial}</div>
                  <div className="user-dropdown-info">
                    <span className="user-dropdown-name">{userDisplayName}</span>
                    <span className="user-dropdown-email">{user.email}</span>
                  </div>
                </div>
                <div className="user-dropdown-divider" role="separator" />
                <button
                  className="user-dropdown-item"
                  role="menuitem"
                  onClick={() => navigateTo('profile')}
                >
                  <User size={15} aria-hidden="true" />
                  <span>{t('profileTitle')}</span>
                </button>
                <button
                  className="user-dropdown-item"
                  role="menuitem"
                  onClick={() => navigateTo('reports')}
                >
                  <FileText size={15} aria-hidden="true" />
                  <span>{t('profileMyReports')}</span>
                </button>
                <div className="user-dropdown-divider" role="separator" />
                <button
                  className="user-dropdown-item user-dropdown-signout"
                  role="menuitem"
                  onClick={() => { signOut(); setShowMobileMenu(false); }}
                >
                  <LogOut size={15} aria-hidden="true" />
                  <span>{t('profileSignOut')}</span>
                </button>
              </div>
            )}
          </div>
        ) : (
          <button
            className="btn btn-primary"
            style={{ width: 'auto', padding: '8px 20px', fontSize: '13px' }}
            onClick={() => setShowAuth(true)}
            aria-label={t('authSignInBtn')}
          >
            <LogIn size={14} aria-hidden="true" /> {t('authSignInBtn')}
          </button>
        )}

        {/* Auth Modal */}
        {showAuth && <AuthModal onClose={() => setShowAuth(false)} />}

        {/* Hamburger — visible on mobile */}
        <button
          className="hamburger-btn"
          onClick={() => setShowMobileMenu(!showMobileMenu)}
          aria-expanded={showMobileMenu}
          aria-label={showMobileMenu ? 'Close menu' : 'Open menu'}
          aria-controls="mobile-nav"
        >
          {showMobileMenu ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {/* Mobile Menu Overlay */}
      {showMobileMenu && (
        <nav
          id="mobile-nav"
          className="mobile-menu"
          role="navigation"
          aria-label="Mobile navigation"
        >
          <div className="mobile-menu-items">
            {navItems.map(item => (
              <button
                key={item.key}
                className={`mobile-nav-item ${isActive(item.view) ? 'active' : ''}`}
                onClick={() => navigateTo(item.view)}
                aria-current={isActive(item.view) ? 'page' : undefined}
              >
                <item.icon size={18} aria-hidden="true" />
                <span>{item.label}</span>
              </button>
            ))}
            {user && (
              <button
                className={`mobile-nav-item`}
                onClick={() => navigateTo('profile')}
              >
                <User size={18} aria-hidden="true" />
                <span>{t('profileTitle')}</span>
              </button>
            )}
          </div>

          {/* User actions in mobile menu */}
          {user && (
            <div className="mobile-menu-user">
              <div className="mobile-menu-user-info">
                <div className="mobile-user-avatar">{userInitial}</div>
                <div>
                  <div className="mobile-user-name">{userDisplayName}</div>
                  <div className="mobile-user-email">{user.email}</div>
                </div>
              </div>
              <button
                className="mobile-nav-item mobile-signout"
                onClick={() => { signOut(); setShowMobileMenu(false); }}
              >
                <LogOut size={18} aria-hidden="true" />
                <span>{t('profileSignOut')}</span>
              </button>
            </div>
          )}
        </nav>
      )}
    </header>
  );
}
