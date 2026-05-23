import { Suspense } from 'react';
import Header from './components/Header';
import Footer from './components/Footer';
import LoadingSpinner from './components/LoadingSpinner';
import { useAppState } from './hooks/useAppState';
import { AuthProvider, useAuth } from './context/AuthContext';
import LandingPage from './pages/LandingPage';
import UploadPage from './pages/UploadPage';
import DashboardPage from './pages/DashboardPage';
import DsaPortal from './pages/DsaPortal';
import ReportsPage from './pages/ReportsPage';
import PaymentPage from './pages/PaymentPage';
import ProfilePage from './pages/ProfilePage';

function AppContent() {
  const s = useAppState();
  const { user, signOut } = useAuth();

  if (s.loading) {
    return (
      <div className="uploader-card" style={{ maxWidth: '640px', marginTop: '60px', margin: '60px auto 0' }} role="status" aria-live="polite" aria-label={s.t('analyzing')}>
        <LoadingSpinner text={s.t('analyzing')} subtext={s.loadingStep} />
      </div>
    );
  }

  const renderPage = () => {
    switch (s.currentView) {
      case 'landing': return <LandingPage t={s.t} selectPlan={s.selectPlan} />;
      case 'uploader': return <UploadPage t={s.t} selectedPlan={s.selectedPlan} planKey={s.planKey} setCurrentView={s.setCurrentView} processFile={s.processFile} />;
      case 'dashboard': return s.reportData ? <DashboardPage t={s.t} reportData={s.reportData} getHealthColors={s.getHealthColors} handleDownloadPDF={s.handleDownloadPDF} downloading={s.downloading} checkedTasks={s.checkedTasks} handleToggleTask={s.handleToggleTask} simulatorResolutions={s.simulatorResolutions} setSimulatorResolutions={s.setSimulatorResolutions} utilizationSlider={s.utilizationSlider} setUtilizationSlider={s.setUtilizationSlider} simulatedScore={s.simulatedScore} simulatedScoreDelta={s.simulatedScoreDelta} /> : <LandingPage t={s.t} selectPlan={s.selectPlan} />;
      case 'dsa': return <DsaPortal t={s.t} planKey={s.planKey} getHealthColors={s.getHealthColors} />;
      case 'payment': return <PaymentPage t={s.t} selectedPlan={s.selectedPlan} planKey={s.planKey} setCurrentView={s.setCurrentView} />;
      case 'reports': return <ReportsPage t={s.t} setCurrentView={s.setCurrentView} setReportData={s.setReportData} />;
      case 'profile': return <ProfilePage />;
      default: return <LandingPage t={s.t} selectPlan={s.selectPlan} />;
    }
  };

  return (
    <>
      <Header lang={s.lang} setLang={s.setLang} t={s.t} currentView={s.currentView} setCurrentView={s.setCurrentView} reportData={s.reportData} handleReset={s.handleReset} user={user} signOut={signOut} />
      <main id="main-content" style={{ flexGrow: 1 }}>
        {s.error && <div className="error-banner" role="alert" aria-live="assertive"><span>{s.error}</span></div>}
        <Suspense fallback={<LoadingSpinner text="" subtext="" />}>
          {renderPage()}
        </Suspense>
      </main>
      <Footer t={s.t} />
    </>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
