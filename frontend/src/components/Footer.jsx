/**
 * CLYR v2 — Footer Component
 */
export default function Footer({ t }) {
  return (
    <footer className="footer" role="contentinfo">
      <div className="footer-inner">
        <div className="footer-brand">
          <span className="footer-logo">CLYR</span>
          <span className="footer-tagline">{t('demystify') || 'CIBIL ka tod-fod, asaan bhasha mein'}</span>
        </div>
        <div className="footer-links">
          <button onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} className="footer-link">
            {t('home') || 'Home'}
          </button>
          <a href="#features" className="footer-link">Features</a>
          <a href="#pricing" className="footer-link">Pricing</a>
          <a href="#faq" className="footer-link">FAQ</a>
        </div>
        <div className="footer-bottom">
          <span>© {new Date().getFullYear()} CLYR. All rights reserved.</span>
          <span className="footer-secure">🔒 256-bit SSL Encrypted</span>
        </div>
      </div>
    </footer>
  );
}
