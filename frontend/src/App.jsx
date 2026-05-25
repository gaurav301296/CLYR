/**
 * CLYR v2 — Main App Component
 * World-class UI architecture: clean routing, state management, error boundaries.
 */
import { Suspense } from 'react';
import Header from './components/Header';
import Footer from './components/Footer';
import { AuthProvider, useAuth } from './context/AuthContext';
import LoadingSpinner from './components/LoadingSpinner';

// Pages
import LandingPage from './pages/LandingPage';
import UploadPage from './pages/UploadPage';
import DashboardPage from './pages/DashboardPage';
import PaymentPage from './pages/PaymentPage';
import ReportsPage from './pages/ReportsPage';
import ProfilePage from './pages/ProfilePage';
import AdminPage from './pages/AdminPage';
import DsaPortal from './pages/DsaPortal';
import NotFoundPage from './pages/NotFoundPage';
import AuthModal from './components/AuthModal';

// Hook for app state
import { useAppState } from './hooks/useAppState';

function AppContent() {
  const s = useAppState();
  const { user } = useAuth();

  if (s.loading) {
    return (
      <div className="loading-screen" role="status" aria-live="polite">
        <LoadingSpinner text={s.t('analyzing')} subtext={s.loadingStep} />
      </div>
    );
  }

  const renderPage = () => {
    switch (s.currentView) {
      case 'landing':
        return <LandingPage t={s.t} selectPlan={s.selectPlan} user={user} />;
      case 'uploader':
        return <UploadPage t={s.t} selectedPlan={s.selectedPlan} planKey={s.planKey} setCurrentView={s.setCurrentView} processFile={s.processFile} />;
      case 'dashboard':
        return s.reportData ? (
          <DashboardPage
            t={s.t}
            reportData={s.reportData}
            getHealthColors={s.getHealthColors}
            handleDownloadPDF={s.handleDownloadPDF}
            downloading={s.downloading}
            checkedTasks={s.checkedTasks}
            handleToggleTask={s.handleToggleTask}
            simulatorResolutions={s.simulatorResolutions}
            setSimulatorResolutions={s.setSimulatorResolutions}
            utilizationSlider={s.utilizationSlider}
            setUtilizationSlider={s.setUtilizationSlider}
            simulatedScore={s.simulatedScore}
            simulatedScoreDelta={s.simulatedScoreDelta}
          />
        ) : (
          <LandingPage t={s.t} selectPlan={s.selectPlan} user={user} />
        );
      case 'payment':
        return <PaymentPage t={s.t} selectedPlan={s.selectedPlan} planKey={s.planKey} setCurrentView={s.setCurrentView} handlePaymentSuccess={s.handlePaymentSuccess} />;
      case 'reports':
        return <ReportsPage t={s.t} setCurrentView={s.setCurrentView} setReportData={s.setReportData} />;
      case 'profile':
        return <ProfilePage />;
      case 'admin':
        return <AdminPage t={s.t} />;
      case 'dsa':
        return <DsaPortal t={s.t} planKey={s.planKey} getHealthColors={s.getHealthColors} />;
      default:
        return <NotFoundPage setCurrentView={s.setCurrentView} />;
    }
  };

  return (
    <div className="app-layout">
      <Header
        lang={s.lang}
        setLang={s.setLang}
        t={s.t}
        currentView={s.currentView}
        setCurrentView={s.setCurrentView}
        reportData={s.reportData}
        handleReset={s.handleReset}
        user={user}
      />
      <main id="main-content" className="main-content">
        {s.error && (
          <div className="error-banner" role="alert" aria-live="assertive">
            <span>{s.error}</span>
            <button onClick={() => s.setError(null)} className="error-dismiss" aria-label="Dismiss error">×</button>
          </div>
        )}
        <Suspense fallback={<LoadingSpinner text="" subtext="" />}>
          {renderPage()}
        </Suspense>
      </main>
      <Footer t={s.t} />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
