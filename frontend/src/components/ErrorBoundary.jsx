import { Component } from 'react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
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
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>Something went wrong</div>
          <p style={{ color: 'var(--text-muted)', marginBottom: '24px', maxWidth: '400px' }}>
            An unexpected error occurred. Please refresh the page and try again.
          </p>
          <button className="btn btn-primary" onClick={() => {
            this.setState({ hasError: false, error: null });
            window.location.reload();
          }}>
            Refresh Page
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
