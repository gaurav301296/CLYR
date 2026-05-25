/**
 * CLYR v2 — Error Boundary
 * Catches React errors and shows a friendly fallback.
 */
import { Component } from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('CLYR Error Boundary caught:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', padding: '24px', textAlign: 'center' }}>
          <AlertCircle size={48} style={{ color: 'var(--color-red)', marginBottom: '16px' }} />
          <h2 style={{ fontSize: '20px', fontWeight: 700, marginBottom: '8px' }}>Kuch Galat Ho Gaya</h2>
          <p style={{ color: 'var(--text-muted)', marginBottom: '24px', maxWidth: '400px' }}>
            Sorry, kuch technical problem aa gayi. Page refresh karke phir se try karo.
          </p>
          <button className="btn btn-primary" onClick={this.handleReset}>
            <RefreshCw size={16} /> Page Refresh Karo
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
