import { useState, useRef, useCallback } from 'react';
import { UploadCloud, Sparkles, AlertCircle } from 'lucide-react';
import { apiUpload } from '../api/client';
import { useAuth } from '../context/AuthContext';

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ALLOWED_TYPE = 'application/pdf';

function validateFile(file) {
  if (!file) return 'Please select a file';
  if (file.type !== ALLOWED_TYPE) return 'Only PDF files are accepted';
  if (file.size > MAX_FILE_SIZE) return 'File size must be under 10MB';
  return '';
}

export default function UploadPage({ t, selectedPlan, planKey, setCurrentView, processFile }) {
  const { user } = useAuth();
  const [fileError, setFileError] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const inputRef = useRef(null);

  const handleFile = useCallback(async (file) => {
    setFileError('');

    const error = validateFile(file);
    if (error) {
      setFileError(error);
      if (inputRef.current) inputRef.current.value = '';
      return;
    }

    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      await apiUpload('/uploads', formData);
      await processFile(file);
    } catch (err) {
      setFileError(err.message || 'Upload failed. Please try again.');
      if (inputRef.current) inputRef.current.value = '';
    } finally {
      setIsUploading(false);
    }
  }, [processFile]);

  const handleChange = useCallback((e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  }, [handleFile]);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  }, [handleFile]);

  const selectLabel = selectedPlan ? t(planKey(selectedPlan)) : t('starterPack');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '680px', margin: '0 auto 80px' }}>
      <section className="hero-section" style={{ padding: '0', textAlign: 'center', marginBottom: '8px' }} aria-labelledby="upload-title">
        <h2 className="hero-title" id="upload-title" style={{ fontSize: '32px' }}>{t('uploadTitle')}</h2>
        <p className="hero-subtitle" style={{ fontSize: '15px' }}>{t('uploadSubtitle')}</p>
      </section>

      <div className="uploader-card" role="region" aria-label="File upload">
        {/* Plan info bar */}
        <div style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          marginBottom: '20px', padding: '12px 16px',
          background: 'rgba(255,255,255,0.02)', borderRadius: '8px',
          border: '1px solid var(--border)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={16} style={{ color: 'var(--primary-hover)' }} aria-hidden="true" />
            <span style={{ fontSize: '13.5px', fontWeight: '500', color: 'var(--text-highlight)' }}>
              {t('selectedPlan')}{' '}
              <strong style={{ color: 'var(--primary-hover)' }}>{selectLabel}</strong>
            </span>
          </div>
          <button
            onClick={() => setCurrentView('landing')}
            style={{
              background: 'transparent', border: 'none', color: 'var(--text-muted)',
              fontSize: '12px', cursor: 'pointer', textDecoration: 'underline',
            }}
            aria-label="Change selected plan"
          >
            {t('changePlan')}
          </button>
        </div>

        {/* Drag-and-drop zone */}
        <div
          className={`upload-zone ${isDragging ? 'drag-over' : ''}`}
          onClick={() => inputRef.current?.click()}
          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') inputRef.current?.click(); }}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          role="button"
          tabIndex={0}
          aria-label="Upload credit report PDF. Drag and drop or click to browse."
          style={{
            borderColor: fileError ? 'var(--color-red)' : isDragging ? 'var(--primary)' : undefined,
            background: isDragging ? 'var(--primary-glow)' : undefined,
            opacity: isUploading ? 0.6 : 1,
            pointerEvents: isUploading ? 'none' : 'auto',
          }}
        >
          <input
            ref={inputRef}
            type="file"
            className="file-input"
            accept=".pdf,application/pdf"
            onChange={handleChange}
            aria-label="Choose PDF file"
          />
          <UploadCloud size={48} className="upload-icon" strokeWidth={1.5} aria-hidden="true" />
          <p className="upload-title">
            {isUploading ? t('uploading') || 'Uploading…' : t('dragDrop')}
          </p>
          <p className="upload-hint">{t('orClick')}</p>
        </div>

        {/* Inline error */}
        {fileError && (
          <div
            style={{
              display: 'flex', alignItems: 'center', gap: '8px',
              marginTop: '12px', padding: '10px 14px',
              borderRadius: '8px',
              background: 'var(--color-red-bg)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#fca5a5', fontSize: '13px',
            }}
            role="alert"
          >
            <AlertCircle size={16} style={{ flexShrink: 0 }} aria-hidden="true" />
            <span>{fileError}</span>
          </div>
        )}

        {/* Security note */}
        <div style={{ marginTop: '24px', fontSize: '13px', color: 'var(--text-muted)' }} role="note">
          {t('safeSecure')}
        </div>
      </div>
    </div>
  );
}
