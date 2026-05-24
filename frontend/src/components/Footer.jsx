import { ShieldCheck, Lock, Heart } from 'lucide-react';

export default function Footer({ t }) {
  return (
    <footer className="app-footer" role="contentinfo">
      <p>&copy; {new Date().getFullYear()} CLYR. {t('footerText')}</p>
      <p style={{ marginTop: '4px', fontSize: '12px', color: 'var(--text-muted)' }}>
        {t('footerDisclaimer')}
      </p>
      <div className="footer-trust">
        <div className="footer-trust-item">
          <Lock size={12} /> Bank-level encryption
        </div>
        <div className="footer-trust-item">
          <ShieldCheck size={12} /> Razorpay secured
        </div>
        <div className="footer-trust-item">
          100% Private
        </div>
      </div>
      <p className="footer-madein">
        Made with <Heart size={12} style={{ color: 'var(--color-red)' }} /> in India 🇮🇳
      </p>
    </footer>
  );
}
