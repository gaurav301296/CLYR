import { useState, useMemo } from 'react';
import { ShieldAlert, FileText, AlertTriangle, CheckCircle2, Mail, ArrowRight } from 'lucide-react';
import { joinWaitlist } from '../lib/supabase';
import { trackEvent } from '../lib/analytics';
import { validateEmail } from '../lib/validation';
import AuthModal from '../components/AuthModal';

export default function LandingPage({ t, selectPlan }) {
  const [email, setEmail] = useState('');
  const [waitlistStatus, setWaitlistStatus] = useState(null);
  const [showAuth, setShowAuth] = useState(false);
  const [emailError, setEmailError] = useState('');
  const [emailTouched, setEmailTouched] = useState(false);

  const isEmailValid = useMemo(() => validateEmail(email).valid, [email]);

  const handleEmailChange = (value) => {
    setEmail(value);
    if (emailTouched) {
      const result = validateEmail(value);
      setEmailError(result.error);
    }
  };

  const handleEmailBlur = () => {
    setEmailTouched(true);
    const result = validateEmail(email);
    setEmailError(result.error);
  };

  const handleWaitlist = async (e) => {
    e.preventDefault();
    setEmailTouched(true);

    const result = validateEmail(email);
    if (!result.valid) {
      setEmailError(result.error);
      return;
    }

    setEmailError('');
    setWaitlistStatus('loading');
    try {
      await joinWaitlist(email, 'landing_page');
      setWaitlistStatus('success');
      trackEvent('waitlist_signup', { email });
      setEmail('');
      setEmailTouched(false);
    } catch {
      setWaitlistStatus('error');
    }
    setTimeout(() => setWaitlistStatus(null), 3000);
  };

  return (
    <div className="landing-container">
      {showAuth && <AuthModal onClose={() => setShowAuth(false)} />}

      <section className="hero-section" role="region" aria-labelledby="hero-title">
        <div className="hero-tag" aria-hidden="true">
          <ShieldAlert size={14} /> {t('demystify')}
        </div>
        <h2 className="hero-title" id="hero-title">{t('heroTitle')}</h2>
        <p className="hero-subtitle">{t('heroSubtitle')}</p>

        <form
          onSubmit={handleWaitlist}
          style={{ marginTop: '32px', display: 'flex', gap: '12px', maxWidth: '480px', margin: '32px auto 0' }}
          aria-label="Waitlist signup"
          noValidate
        >
          <div style={{ position: 'relative', flex: 1 }}>
            <Mail size={16} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} aria-hidden="true" />
            <input
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => handleEmailChange(e.target.value)}
              onBlur={handleEmailBlur}
              aria-label="Email address"
              aria-invalid={emailTouched && !!emailError}
              aria-describedby={emailTouched && emailError ? 'email-error' : undefined}
              style={{
                width: '100%', padding: '14px 14px 14px 42px',
                borderRadius: '10px', border: `1px solid ${emailTouched && emailError ? '#ef4444' : 'var(--border)'}`,
                background: 'var(--bg-card)', color: 'var(--text-highlight)',
                fontSize: '14px', outline: 'none',
              }}
            />
          </div>
          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: 'auto', padding: '14px 24px' }}
            disabled={waitlistStatus === 'loading' || !isEmailValid}
          >
            {waitlistStatus === 'loading' ? '...' : <><ArrowRight size={16} aria-hidden="true" /> Get Started</>}
          </button>
        </form>
        {emailTouched && emailError && (
          <p id="email-error" style={{ color: '#ef4444', fontSize: '12px', marginTop: '6px', textAlign: 'left', maxWidth: '480px', margin: '6px auto 0' }} role="alert">
            {emailError}
          </p>
        )}
        {waitlistStatus === 'success' && <p style={{ color: 'var(--color-green)', fontSize: '13px', marginTop: '8px' }} role="status">You are on the list! We will notify you when we launch.</p>}
        {waitlistStatus === 'error' && <p style={{ color: 'var(--color-red)', fontSize: '13px', marginTop: '8px' }} role="alert">Something went wrong. Please try again.</p>}

        <button
          onClick={() => setShowAuth(true)}
          style={{ marginTop: '16px', background: 'none', border: 'none', color: 'var(--primary-hover)', fontSize: '13px', cursor: 'pointer', textDecoration: 'underline' }}
          aria-label="Already have an account? Sign in"
        >
          Already have an account? Sign in
        </button>
      </section>

      <section aria-labelledby="features-heading">
        <h2 id="features-heading" className="sr-only">Features</h2>
        <div className="features-grid">
          {[
            { icon: FileText, title: t('featureParserTitle'), desc: t('featureParserDesc'), theme: '' },
            { icon: AlertTriangle, title: t('featureScanTitle'), desc: t('featureScanDesc'), theme: 'red-theme' },
            { icon: CheckCircle2, title: t('featureRoadmapTitle'), desc: t('featureRoadmapDesc'), theme: 'green-theme' },
          ].map((feature, i) => (
            <div key={i} className={`feature-card ${feature.theme}`} role="article">
              <div className="feature-icon-wrapper" aria-hidden="true">
                <feature.icon size={24} />
              </div>
              <h3 className="feature-title">{feature.title}</h3>
              <p className="feature-desc">{feature.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section aria-labelledby="pricing-heading">
        <div className="pricing-title-container">
          <h2 id="pricing-heading">{t('choosePathTitle')}</h2>
          <p style={{ color: 'var(--text-muted)' }}>{t('choosePathSubtitle')}</p>
        </div>
        <div className="pricing-grid" role="list">
          {['Starter', 'Follow-up', 'Recovery'].map((plan) => {
            const isPopular = plan === 'Follow-up';
            const featuresKey = plan === 'Starter' ? ['starterFeature1', 'starterFeature2', 'starterFeature3']
              : plan === 'Follow-up' ? ['followupFeature1', 'followupFeature2', 'followupFeature3']
              : ['recoveryFeature1', 'recoveryFeature2', 'recoveryFeature3'];
            const price = plan === 'Starter' ? 499 : plan === 'Follow-up' ? 799 : 1299;
            const chooseKey = plan === 'Starter' ? 'chooseStarter' : plan === 'Follow-up' ? 'chooseFollowup' : 'chooseRecovery';
            const packKey = plan === 'Starter' ? 'starterPack' : plan === 'Follow-up' ? 'followupPack' : 'recoveryPack';

            return (
              <div key={plan} className={`pricing-card ${isPopular ? 'popular' : ''}`} role="listitem">
                {isPopular && <div className="popular-tag" aria-label="Most popular plan">{t('mostPopular')}</div>}
                <h3 className="plan-name">{t(packKey)}</h3>
                <div className="plan-price-wrapper" aria-label={`₹${price} one-time`}>
                  <span className="plan-currency">₹</span>
                  <span className="plan-price">{price}</span>
                  <span className="plan-price-subtitle">{t('oneTime')}</span>
                </div>
                <ul className="pricing-features" role="list" aria-label={`${t(packKey)} features`}>
                  {featuresKey.map((fk, i) => (
                    <li key={i} className="pricing-feature-item">
                      <CheckCircle2 size={16} aria-hidden="true" />
                      <span>{t(fk)}</span>
                    </li>
                  ))}
                </ul>
                <button
                  className={`btn ${isPopular ? 'btn-primary' : 'btn-secondary'} pricing-btn`}
                  onClick={() => { selectPlan(plan); trackEvent('plan_selected', { plan }); }}
                  aria-label={`${t(chooseKey)} - ₹${price}`}
                >
                  {t(chooseKey)}
                </button>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
