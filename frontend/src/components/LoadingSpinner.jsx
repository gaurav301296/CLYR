/**
 * CLYR v2 — Loading Spinner
 */
export default function LoadingSpinner({ text = 'Loading...', subtext = '' }) {
  return (
    <div className="loading-spinner-container" role="status" aria-live="polite">
      <div className="spinner-large" aria-hidden="true">
        <div className="spinner-ring" />
        <div className="spinner-ring spinner-ring-2" />
        <div className="spinner-dot" />
      </div>
      {text && <p className="loading-text">{text}</p>}
      {subtext && <p className="loading-subtext">{subtext}</p>}
      <span className="sr-only">Loading, please wait...</span>
    </div>
  );
}
