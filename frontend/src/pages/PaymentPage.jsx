import { useState, useCallback } from 'react';
import { CheckCircle2, AlertTriangle, ArrowLeft, Loader2, ShieldCheck, CreditCard } from 'lucide-react';
import { apiFetch } from '../api/client';
import { useAuth } from '../context/AuthContext';

const PLAN_PRICES = {
  'Starter': 499,
  'Follow-up': 799,
  'Recovery': 1299,
};

const PLAN_FEATURES = {
  'Starter': ['starterFeature1', 'starterFeature2', 'starterFeature3'],
  'Follow-up': ['followupFeature1', 'followupFeature2', 'followupFeature3'],
  'Recovery': ['recoveryFeature1', 'recoveryFeature2', 'recoveryFeature3'],
};

function loadRazorpayScript() {
  return new Promise((resolve, reject) => {
    if (window.Razorpay) {
      resolve();
      return;
    }
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.onload = resolve;
    script.onerror = () => reject(new Error('Failed to load Razorpay SDK'));
    document.body.appendChild(script);
  });
}

export default function PaymentPage({ t, selectedPlan, planKey, setCurrentView, handlePaymentSuccess, reportData }) {
  const { user } = useAuth();
  const [status, setStatus] = useState('idle'); // idle | loading | processing | success | error
  const [errorMsg, setErrorMsg] = useState('');

  const planName = selectedPlan || 'Starter';
  const planLabel = t(planKey);
  const price = PLAN_PRICES[planName] || 499;
  const features = PLAN_FEATURES[planName] || PLAN_FEATURES['Starter'];

  const handlePayNow = useCallback(async () => {
    setStatus('loading');
    setErrorMsg('');

    try {
      await loadRazorpayScript();

      // Step 1: Create order via apiFetch
      const order = await apiFetch('/payments/create-order', {
        method: 'POST',
        body: JSON.stringify({ plan: planName, report_id: s.reportData?.id || null }),
      });

      if (!order || !order.order_id) {
        throw new Error('Invalid order response from server');
      }

      const razorpayKeyId = import.meta.env.VITE_RAZORPAY_KEY_ID;

      if (!razorpayKeyId) {
        throw new Error('Razorpay key not configured. Please contact support.');
      }

      // Step 2: Open Razorpay checkout modal
      const options = {
        key: razorpayKeyId,
        amount: order.amount,
        currency: order.currency || 'INR',
        name: 'CLYR',
        description: `${planLabel} - Credit Report Analysis`,
        order_id: order.order_id,
        handler: async (response) => {
          // Step 3: Verify payment
          setStatus('processing');
          try {
            await apiFetch('/payments/verify', {
              method: 'POST',
              body: JSON.stringify({
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature,
              }),
            });
            setStatus('success');
          } catch (verifyErr) {
            setStatus('error');
            setErrorMsg(
              verifyErr.message || 'Payment verification failed. Please contact support.'
            );
          }
        },
        prefill: {
          name: user?.full_name || '',
          email: user?.email || '',
        },
        theme: {
          color: '#2563eb',
        },
        modal: {
          ondismiss: () => {
            if (status === 'loading') {
              setStatus('idle');
            }
          },
        },
      };

      const rzp = new window.Razorpay(options);
      rzp.open();
    } catch (err) {
      setStatus('error');
      setErrorMsg(err.message || 'Something went wrong. Please try again.');
    }
  }, [planName, planLabel, user, status]);

  // Success screen
  if (status === 'success') {
    return (
      <div style={{ maxWidth: '560px', margin: '60px auto 0', textAlign: 'center', padding: '0 16px' }}>
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: '16px',
          padding: '48px 32px',
        }}>
          <div style={{
            width: '72px',
            height: '72px',
            borderRadius: '50%',
            background: 'rgba(16, 185, 129, 0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 24px',
          }}>
            <CheckCircle2 size={36} style={{ color: 'var(--color-green)' }} />
          </div>
          <h2 style={{ fontSize: '24px', fontWeight: '700', color: 'var(--text-highlight)', marginBottom: '12px' }}>
            Payment Successful!
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '15px', marginBottom: '8px' }}>
            Your <strong style={{ color: 'var(--text-highlight)' }}>{planLabel}</strong> plan has been activated.
          </p>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginBottom: '32px' }}>
            Your report is ready. Download your full analysis now.
          </p>
          <button
            className="btn btn-primary"
            onClick={() => handlePaymentSuccess ? handlePaymentSuccess(planName) : setCurrentView('dashboard')}
            style={{ width: 'auto', padding: '14px 32px', fontSize: '15px' }}
          >
            Download Report →
          </button>
        </div>
      </div>
    );
  }

  // Order summary + pay button
  return (
    <div style={{ maxWidth: '560px', margin: '40px auto 0', padding: '0 16px' }}>
      <button
        onClick={() => setCurrentView('landing')}
        style={{
          background: 'transparent',
          border: 'none',
          color: 'var(--text-muted)',
          fontSize: '14px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          marginBottom: '24px',
          padding: '4px 0',
        }}
        aria-label="Go back to plans"
      >
        <ArrowLeft size={16} />
        Back to Plans
      </button>

      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: '16px',
        padding: '32px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
          <div style={{
            width: '44px',
            height: '44px',
            borderRadius: '12px',
            background: 'rgba(37, 99, 235, 0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <CreditCard size={22} style={{ color: 'var(--primary)' }} />
          </div>
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: '700', color: 'var(--text-highlight)', margin: 0 }}>
              Complete Your Purchase
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '13px', margin: 0 }}>
              Secure payment via Razorpay
            </p>
          </div>
        </div>

        {/* Order Summary */}
        <div style={{
          background: 'rgba(255,255,255,0.02)',
          border: '1px solid var(--border)',
          borderRadius: '12px',
          padding: '20px',
          marginBottom: '24px',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', margin: '0 0 4px' }}>Selected Plan</p>
              <p style={{ fontSize: '18px', fontWeight: '600', color: 'var(--text-highlight)', margin: 0 }}>
                {planLabel}
              </p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', margin: '0 0 4px' }}>Total</p>
              <p style={{ fontSize: '28px', fontWeight: '700', color: 'var(--primary)', margin: 0 }}>
                ₹{price}
              </p>
            </div>
          </div>

          <div style={{ borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', margin: '0 0 10px', fontWeight: '500' }}>
              What's included:
            </p>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {features.map((fk, i) => (
                <li key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', color: 'var(--text-highlight)' }}>
                  <CheckCircle2 size={16} style={{ color: 'var(--color-green)', flexShrink: 0 }} />
                  {t(fk)}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Error message */}
        {status === 'error' && errorMsg && (
          <div
            role="alert"
            style={{
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '10px',
              padding: '14px 16px',
              marginBottom: '20px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
            }}
          >
            <AlertTriangle size={18} style={{ color: 'var(--color-red)', flexShrink: 0 }} />
            <span style={{ color: 'var(--color-red)', fontSize: '14px' }}>{errorMsg}</span>
          </div>
        )}

        {/* Pay button */}
        <button
          className="btn btn-primary"
          onClick={handlePayNow}
          disabled={status === 'loading' || status === 'processing'}
          style={{
            width: '100%',
            padding: '16px',
            fontSize: '16px',
            fontWeight: '600',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '10px',
          }}
          aria-label={`Pay ₹${price} for ${planLabel}`}
        >
          {status === 'loading' ? (
            <>
              <Loader2 size={18} className="spinner" style={{ animation: 'spin 1s linear infinite' }} />
              Creating Order...
            </>
          ) : status === 'processing' ? (
            <>
              <Loader2 size={18} className="spinner" style={{ animation: 'spin 1s linear infinite' }} />
              Verifying Payment...
            </>
          ) : (
            <>
              <CreditCard size={18} />
              Pay ₹{price} Now
            </>
          )}
        </button>

        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px',
          marginTop: '16px',
        }}>
          <ShieldCheck size={14} style={{ color: 'var(--text-muted)' }} />
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Secured by Razorpay. Your payment is encrypted and safe.
          </span>
        </div>
      </div>
    </div>
  );
}
