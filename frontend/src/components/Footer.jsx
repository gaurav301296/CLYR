export default function Footer({ t }) {
  return (
    <footer className="app-footer" role="contentinfo">
      <p>&copy; {new Date().getFullYear()} CLYR. {t('footerText')}</p>
      <p style={{ marginTop: '4px', fontSize: '11px', color: 'var(--text-muted)' }}>
        {t('footerDisclaimer')}
      </p>
    </footer>
  );
}
