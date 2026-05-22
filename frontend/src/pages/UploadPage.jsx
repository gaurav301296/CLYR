import { useState } from 'react';
import { UploadCloud, Sparkles, AlertCircle } from 'lucide-react';
import { validateFile } from '../lib/validation';

export default function UploadPage({ t, selectedPlan, planKey, setCurrentView, processFile }) {
  const [fileError, setFileError] = useState('');

  const handleFileChange = async (e) => {
    setFileError('');
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const result = validateFile(file);
      if (!result.valid) {
        setFileError(result.error);
        // Reset the input so the same file can be re-selected
        e.target.value = '';
        return;
      }
      await processFile(file);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px', maxWidth: '680px', margin: '0 auto 80px' }}>
      <section className="hero-section" style={{ padding: '0', textAlign: 'center', marginBottom: '16px' }} aria-labelledby="upload-title">
        <h2 className="hero-title" id="upload-title" style={{ fontSize: '32px' }}>{t('uploadTitle')}</h2>
        <p className="hero-subtitle" style={{ fontSize: '15px' }}>{t('uploadSubtitle')}</p>
      </section>

      <div className="uploader-card" role="region" aria-label="File upload">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', padding: '12px 16px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', border: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={16} style={{ color: 'var(--primary-hover)' }} aria-hidden="true" />
            <span style={{ fontSize: '13.5px', fontWeight: '500', color: 'var(--text-highlight)' }}>
              {t('selectedPlan')} <strong style={{ color: 'var(--primary-hover)' }}>{selectedPlan ? t(planKey(selectedPlan)) : t('starterPack')}</strong>
            </span>
          </div>
          <button
            onClick={() => setCurrentView('landing')}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', fontSize: '12px', cursor: 'pointer', textDecoration: 'underline' }}
            aria-label="Change selected plan"
          >
            {t('changePlan')}
          </button>
        </div>

        <div
          className="upload-zone"
          onClick={() => document.getElementById('pdf-upload').click()}
          role="button"
          tabIndex={0}
          aria-label="Upload credit report PDF. Drag and drop or click to browse."
          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') document.getElementById('pdf-upload').click(); }}
          style={{ borderColor: fileError ? '#ef4444' : undefined }}
        >
          <input type="file" id="pdf-upload" className="file-input" accept=".pdf" onChange={handleFileChange} aria-label="Choose PDF file" />
          <UploadCloud size={48} className="upload-icon" strokeWidth={1.5} aria-hidden="true" />
          <p className="upload-title">{t('dragDrop')}</p>
          <p className="upload-hint">{t('orClick')}</p>
        </div>

        {fileError && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginTop: '12px',
              padding: '10px 14px',
              borderRadius: '8px',
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#fca5a5',
              fontSize: '13px',
            }}
            role="alert"
          >
            <AlertCircle size={16} style={{ flexShrink: 0 }} aria-hidden="true" />
            <span>{fileError}</span>
          </div>
        )}

        <div style={{ marginTop: '24px', fontSize: '13px', color: 'var(--text-muted)' }} role="note">
          {t('safeSecure')}
        </div>
      </div>
    </div>
  );
}
