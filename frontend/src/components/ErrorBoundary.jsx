import { Component } from 'react';
import logger from '../lib/logger';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    logger.error('ErrorBoundary caught', {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo?.componentStack,
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          role="alert"
          aria-live="assertive"
          style={{
            display: 'flex', flexDirection: 'column', alignItems: 'center',
            justifyContent: 'center', minHeight: '60vh', padding: '40px 24px',
            textAlign: 'center'
          }}
        >
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>😅</div>
          <h2 style={{ fontSize: '22px', marginBottom: '12px', color: 'var(--text-highlight)' }}>
            Oops! Kuch ho gaya...
          </h2>
          <p style={{ color: 'var(--text-muted)', marginBottom: '24px', maxWidth: '400px' }}>
            Koi unexpected error aa gayi. Refresh karke dobara try karo. Agar problem rahi, toh humein batana — hum fix kar lenge.
          </p>
          <button className="btn btn-primary" onClick={() => {
            this.setState({ hasError: false, error: null });
            window.location.reload();
          }}>
            Refresh Karo
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
