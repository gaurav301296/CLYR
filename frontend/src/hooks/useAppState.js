import { useState, useEffect, useCallback, useMemo } from 'react';
import { translations, LANGUAGES } from '../i18n/translations';

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8005/api";

export function useAppState() {
  const [lang, setLang] = useState('en');
  const [currentView, setCurrentView] = useState('landing');
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState("");
  const [reportData, setReportData] = useState(null);
  const [error, setError] = useState(null);
  const [checkedTasks, setCheckedTasks] = useState(new Set());
  const [downloading, setDownloading] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [simulatorResolutions, setSimulatorResolutions] = useState(new Set());
  const [utilizationSlider, setUtilizationSlider] = useState(60);

  const t = useCallback((key) => {
    return (translations[lang] && translations[lang][key]) || (translations['en'] && translations['en'][key]) || key;
  }, [lang]);

  const planKey = useCallback((plan) => {
    const map = { 'Starter': 'starterPack', 'Follow-up': 'followupPack', 'Recovery': 'recoveryPack' };
    return map[plan] || 'starterPack';
  }, []);

  const loadingStages = useMemo(() => [
    t('loadingStage1'), t('loadingStage2'), t('loadingStage3'),
    t('loadingStage4'), t('loadingStage5'), t('loadingStage6')
  ], [t]);

  useEffect(() => { document.documentElement.lang = lang; }, [lang]);

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

  const processFile = useCallback(async (targetFile) => {
    setLoading(true);
    setError(null);
    setReportData(null);
    setCheckedTasks(new Set());
    const formData = new FormData();
    formData.append("file", targetFile);
    try {
      const response = await fetch(`${API_BASE}/upload`, { method: "POST", body: formData });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to process the credit report PDF.');
      }
      const data = await response.json();
      setReportData(data);
      setCurrentView('dashboard');
    } catch (err) {
      console.error(err);
      setError(err.message || 'An unexpected error occurred while parsing the credit report.');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleDownloadPDF = useCallback(async () => {
    if (!reportData) return;
    setDownloading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/download`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...reportData, language: lang })
      });
      if (!response.ok) throw new Error('Failed to compile and download PDF.');
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `CLYR_Roadmap_${reportData.customer_name.replace(/\s+/g, '_')}.pdf`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      console.error(err);
      setError('Failed to download PDF. Please try again.');
    } finally {
      setDownloading(false);
    }
  }, [reportData, lang]);

  const handleReset = useCallback(() => {
    setReportData(null);
    setError(null);
    setCheckedTasks(new Set());
    setSimulatorResolutions(new Set());
    setCurrentView('landing');
    setSelectedPlan(null);
  }, []);

  const handleToggleTask = useCallback((index) => {
    setCheckedTasks(prev => {
      const next = new Set(prev);
      if (next.has(index)) next.delete(index); else next.add(index);
      return next;
    });
  }, []);

  const selectPlan = useCallback((plan) => {
    setSelectedPlan(plan);
    setCurrentView('payment');
  }, []);

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
          const isCritical = ['critical', 'red', 'major'].includes(issue.type.toLowerCase());
          score += isCritical ? 45 : 25;
        }
      });
    }
    score += getUtilPoints(utilizationSlider) - getUtilPoints(60);
    return Math.max(300, Math.min(900, score));
  }, [reportData, simulatorResolutions, utilizationSlider, getUtilPoints]);

  const simulatedScoreDelta = reportData ? simulatedScore - reportData.score : 0;

  const getHealthColors = useCallback((score) => {
    if (score >= 750) return { name: "Excellent", class: "green", stroke: "#10b981", percent: (score / 900) * 100 };
    if (score >= 700) return { name: "Good", class: "green", stroke: "#10b981", percent: (score / 900) * 100 };
    if (score >= 650) return { name: "Fair", class: "yellow", stroke: "#f59e0b", percent: (score / 900) * 100 };
    return { name: "Needs Attention", class: "red", stroke: "#ef4444", percent: (score / 900) * 100 };
  }, []);

  return {
    lang, setLang, t, planKey,
    currentView, setCurrentView,
    loading, loadingStep,
    reportData,
    error,
    checkedTasks, setCheckedTasks,
    downloading,
    selectedPlan,
    simulatorResolutions, setSimulatorResolutions,
    utilizationSlider, setUtilizationSlider,
    processFile, handleDownloadPDF, handleReset, handleToggleTask, selectPlan,
    simulatedScore, simulatedScoreDelta, getHealthColors, setReportData,
  };
}
