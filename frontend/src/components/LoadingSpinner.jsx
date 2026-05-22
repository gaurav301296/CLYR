export default function LoadingSpinner({ text, subtext }) {
  return (
    <div className="loading-container" role="status" aria-live="polite" aria-busy="true">
      <div className="spinner" aria-hidden="true"></div>
      {text && <p className="loading-text">{text}</p>}
      {subtext && <p className="loading-subtext" aria-live="polite">{subtext}</p>}
    </div>
  );
}
