/**
 * CLYR v2 — App State Hook
 * Central state management for the entire frontend.
 *
 * User flow:
 * 1. Landing → click "Upload" → UploadPage
 * 2. Upload PDF → analysis starts → DashboardPage (free preview)
 * 3. Dashboard shows score, issues, but PDF download requires payment
 * 4. Click download → PaymentPage → Razorpay → success → can download
 */
import { useState, useEffect, useCallback, useMemo } from 'react';
import { apiFetch, apiUpload } from '../api/client';
import { translations } from '../i18n/translations';

export function useAppState() {
  const [lang, setLang] = useState(() => localStorage.getItem('clyr_lang') || 'en');
  const [currentView, setCurrentView] = useState('landing');
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState('');
  const [reportData, setReportData] = useState(() => {
    // Restore from session storage
    try {
      const saved = sessionStorage.getItem('clyr_report');
      return saved ? JSON.parse(saved) : null;
    } catch { return null; }
  });
  const [error, setError] = useState(null);
  const [checkedTasks, setCheckedTasks] = useState(new Set());
  const [downloading, setDownloading] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState('Starter');
  const [paymentDone, setPaymentDone] = useState(false);
  const [simulatorResolutions, setSimulatorResolutions] = useState(new Set());
  const [utilizationSlider, setUtilizationSlider] = useState(60);

  // Translation function — looks up key in current language, falls back to English, then to key itself
  const t = useCallback((key) => {
    const langTranslations = translations[lang] || translations['en'] || {};
    return langTranslations[key] || translations['en']?.[key] || key;
  }, [lang]);

  const planKey = useCallback((plan) => {
    const map = { 'Starter': 'starterPack', 'Follow-up': 'followupPack', 'Recovery': 'recoveryPack' };
    return map[plan] || 'starterPack';
  }, []);

  const loadingStages = useMemo(() => [
    t('loadingStage1'), t('loadingStage2'), t('loadingStage3'),
    t('loadingStage4'), t('loadingStage5'), t('loadingStage6')
  ], [t]);

  // Persist language and report data
  useEffect(() => {
    localStorage.setItem('clyr_lang', lang);
    document.documentElement.lang = lang;
  }, [lang]);

  useEffect(() => {
    if (reportData) {
      sessionStorage.setItem('clyr_report', JSON.stringify(reportData));
    }
  }, [reportData]);

  // Loading animation
  useEffect(() => {
    let interval;
    if (loading) {
      let stageIndex = 0;
      setLoadingStep(loadingStages[0]);
      interval = setInterval(() => {
        stageIndex = (stageIndex + 1) % loadingStages.length;
        setLoadingStep(loadingStages[stageIndex]);
      }, 2500);
    }
    return () => clearInterval(interval);
  }, [loading, loadingStages]);

  // File upload + analysis
  const processFile = useCallback(async (file) => {
    setLoading(true);
    setError(null);
    setReportData(null);
    setPaymentDone(false);
    setCheckedTasks(new Set());

    try {
      const formData = new FormData();
      formData.append('file', file);

      const data = await apiUpload('/reports/upload', formData);
      setReportData(data);
      setCurrentView('dashboard');
    } catch (err) {
      setError(err.message || 'Failed to process the credit report. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  // PDF download — requires payment
  const handleDownloadPDF = useCallback(async () => {
    if (!reportData) return;

    // If already paid, download directly
    if (paymentDone) {
      await doDownload();
      return;
    }

    // Otherwise, go to payment
    setCurrentView('payment');
  }, [reportData, paymentDone]);

  const doDownload = async () => {
    if (!reportData) return;
    setDownloading(true);
    setError(null);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE || 'http://localhost:8005/api'}/pdf/download/${reportData.id}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('clyr_token') || ''}`,
        },
      });

      if (!response.ok) throw new Error('Download failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `CLYR_Report_${(reportData.customer_name || 'report').replace(/\s+/g, '_')}.pdf`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to download PDF. Please try again.');
    } finally {
      setDownloading(false);
    }
  };

  // Payment success callback
  const handlePaymentSuccess = useCallback((plan) => {
    setPaymentDone(true);
    setSelectedPlan(plan);
    setCurrentView('dashboard');
  }, []);

  // Reset everything
  const handleReset = useCallback(() => {
    setReportData(null);
    setError(null);
    setCheckedTasks(new Set());
    setSimulatorResolutions(new Set());
    setPaymentDone(false);
    setCurrentView('landing');
    setSelectedPlan('Starter');
    sessionStorage.removeItem('clyr_report');
  }, []);

  // Toggle checklist item
  const handleToggleTask = useCallback((index) => {
    setCheckedTasks(prev => {
      const next = new Set(prev);
      if (next.has(index)) next.delete(index); else next.add(index);
      return next;
    });
  }, []);

  // Plan selection from landing
  const selectPlan = useCallback((plan) => {
    setSelectedPlan(plan);
    // Go directly to upload — payment happens after analysis
    setCurrentView('uploader');
  }, []);

  // Score simulation
  const getUtilPoints = useCallback((val) => {
    if (val < 10) return 35;
    if (val <= 30) return 20;
    if (val <= 50) return 5;
    if (val <= 70) return -10;
    if (val <= 90) return -30;
    return -50;
  }, []);

  const simulatedScore = useMemo(() => {
    if (!reportData) return 300;
    let score = reportData.score;
    if (reportData.issues) {
      reportData.issues.forEach((issue, idx) => {
        if (simulatorResolutions.has(idx)) {
          const isCritical = ['critical', 'red', 'major'].includes((issue.type || '').toLowerCase());
          score += isCritical ? 45 : 25;
        }
      });
    }
    score += getUtilPoints(utilizationSlider) - getUtilPoints(60);
    return Math.max(300, Math.min(900, score));
  }, [reportData, simulatorResolutions, utilizationSlider, getUtilPoints]);

  const simulatedScoreDelta = reportData ? simulatedScore - reportData.score : 0;

  const getHealthColors = useCallback((score) => {
    if (score >= 750) return { name: 'Excellent', class: 'green', stroke: '#10b981', percent: (score / 900) * 100 };
    if (score >= 700) return { name: 'Good', class: 'green', stroke: '#10b981', percent: (score / 900) * 100 };
    if (score >= 650) return { name: 'Fair', class: 'yellow', stroke: '#f59e0b', percent: (score / 900) * 100 };
    return { name: 'Needs Attention', class: 'red', stroke: '#ef4444', percent: (score / 900) * 100 };
  }, []);

  return {
    lang, setLang, t, planKey,
    currentView, setCurrentView,
    loading, loadingStep,
    reportData, setReportData,
    error, setError,
    checkedTasks, setCheckedTasks,
    downloading,
    selectedPlan, selectPlan,
    paymentDone, handlePaymentSuccess,
    simulatorResolutions, setSimulatorResolutions,
    utilizationSlider, setUtilizationSlider,
    processFile, handleDownloadPDF, handleReset, handleToggleTask,
    simulatedScore, simulatedScoreDelta, getHealthColors,
  };
}
