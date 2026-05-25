/**
 * CLYR v2 — 404 Not Found Page
 */
import { Home, AlertCircle } from 'lucide-react';

export default function NotFoundPage({ setCurrentView }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', padding: '24px', textAlign: 'center' }}>
      <AlertCircle size={64} style={{ color: 'var(--text-muted)', marginBottom: '24px' }} />
      <h1 style={{ fontSize: '72px', fontWeight: 800, color: 'var(--primary)', lineHeight: 1, marginBottom: '8px' }}>404</h1>
      <h2 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '12px' }}>Page Nahi Mila</h2>
      <p style={{ color: 'var(--text-muted)', fontSize: '16px', maxWidth: '400px', marginBottom: '32px' }}>
        Yeh page exist nahi karta. Shayad URL galat hai, ya page move ho gaya hai.
      </p>
      <button
        className="btn btn-primary"
        onClick={() => setCurrentView('landing')}
        style={{ width: 'auto', padding: '14px 32px', fontSize: '15px' }}
      >
        <Home size={16} /> Home Par Jao
      </button>
    </div>
  );
}
