/**
 * CLYR v2 — Landing Page
 * World-class conversion-focused landing page.
 * No fake numbers. No hype. Just clear value + social proof that's real.
 */
import { useState, useMemo } from 'react';
import { ShieldCheck, FileText, AlertTriangle, CheckCircle2, ArrowRight, Sparkles, Lock, Globe, TrendingUp, CreditCard } from 'lucide-react';
import { config } from '../config';
import AuthModal from '../components/AuthModal';

const PLAN_PRICES = { Starter: 499, 'Follow-up': 799, Recovery: 1299 };

const PLAN_FEATURES = {
  Starter: ['starterFeature1', 'starterFeature2', 'starterFeature3', 'starterFeature4'],
  'Follow-up': ['followupFeature1', 'followupFeature2', 'followupFeature3', 'followupFeature4', 'followupFeature5'],
  Recovery: ['recoveryFeature1', 'recoveryFeature2', 'recoveryFeature3', 'recoveryFeature4', 'recoveryFeature5'],
};

export default function LandingPage({ t, selectPlan, user }) {
  const [email, setEmail] = useState('');
  const [waitlistStatus, setWaitlistStatus] = useState(null);
  const [showAuth, setShowAuth] = useState(false);
  const [emailError, setEmailError] = useState('');
  const [emailTouched, setEmailTouched] = useState(false);

  const isEmailValid = useMemo(() => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email), [email]);

  const handleEmailChange = (value) => {
    setEmail(value);
    if (emailTouched) {
      const result = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
      setEmailError(result ? '' : 'Please enter a valid email');
    }
  };

  const handleWaitlist = async (e) => {
    e.preventDefault();
    setEmailTouched(true);
    if (!isEmailValid) {
      setEmailError('Please enter a valid email');
      return;
    }
    setEmailError('');
    setWaitlistStatus('loading');
    try {
      const { apiFetch } = await import('../api/client');
      await apiFetch('/waitlist', {
        method: 'POST',
        body: JSON.stringify({ email, source: 'landing_page' }),
      });
      setWaitlistStatus('success');
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

      {/* Hero Section */}
      <section className="hero-section" role="region" aria-labelledby="hero-title">
        <div className="hero-tag" aria-hidden="true">
          <Sparkles size={14} /> {t('demystify') || 'CIBIL ka tod-fod, asaan bhasha mein'}
        </div>
        <h1 className="hero-title" id="hero-title">
          {t('heroTitle') || 'Teri CIBIL report upload karo. Baaki hum sambhal lenge.'}
        </h1>
        <p className="hero-subtitle">
          {t('heroSubtitle') || 'Gandi English, confusing tables, bank jaisi bhasha. Bas report daal do. Hinglish mein samjha denge kya galat hai, kya fix karna hai, aur score kaise badh jaayega.'}
        </p>

        {!user ? (
          <form
            onSubmit={handleWaitlist}
            className="hero-cta"
            aria-label="Waitlist signup"
            noValidate
          >
            <div className="hero-input-wrap">
              <input
                type="email"
                placeholder="Apna email daalo..."
                value={email}
                onChange={(e) => handleEmailChange(e.target.value)}
                onBlur={() => {
                  setEmailTouched(true);
                  if (email && !isEmailValid) setEmailError('Please enter a valid email');
                }}
                aria-label="Email address"
                aria-invalid={emailTouched && !!emailError}
                className={`hero-input ${emailTouched && emailError ? 'error' : ''}`}
              />
            </div>
            <button
              type="submit"
              className="btn btn-primary btn-hero"
              disabled={waitlistStatus === 'loading' || !isEmailValid}
            >
              {waitlistStatus === 'loading' ? (
                <span className="spinner" />
              ) : (
                <><ArrowRight size={16} aria-hidden="true" /> Shuru Karo</>
              )}
            </button>
          </form>
        ) : (
          <button
            onClick={() => selectPlan('Starter')}
            className="btn btn-primary btn-hero"
          >
            <CreditCard size={16} aria-hidden="true" /> Report Upload Karo — ₹499
          </button>
        )}

        {emailTouched && emailError && (
          <p className="hero-error" role="alert">{emailError}</p>
        )}
        {waitlistStatus === 'success' && (
          <p className="hero-success" role="status">✓ Mail pe confirmation aayega. Spam folder check karna mat bhulna.</p>
        )}
        {waitlistStatus === 'error' && (
          <p className="hero-error" role="alert">Kuch galat ho gaya. Phir se try karo.</p>
        )}

        {!user && (
          <button
            onClick={() => setShowAuth(true)}
            className="hero-signin-link"
            aria-label="Already have an account? Sign in"
          >
            Account hai? Sign in karo
          </button>
        )}
      </section>

      {/* Trust Indicators — REAL, not fake */}
      <section className="trust-bar" aria-label="Trust indicators">
        <div className="trust-item">
          <Lock size={16} aria-hidden="true" />
          <span>100% Encrypted</span>
        </div>
        <div className="trust-item">
          <ShieldCheck size={16} aria-hidden="true" />
          <span>Data Store Nahi Hota</span>
        </div>
        <div className="trust-item">
          <Globe size={16} aria-hidden="true" />
          <span>11 Bhasha Mein</span>
        </div>
      </section>

      {/* Features Grid */}
      <section className="features-section" aria-labelledby="features-heading">
        <h2 id="features-heading" className="section-title">Kya Hota Hai Upload Ke Baad?</h2>
        <div className="features-grid">
          {[
            { icon: FileText, title: 'CIBIL ka Jadoo Tod', desc: 'Woh 12-page jungli report ko clean, simple dashboard mein badal dete hain. Zero jargon.', theme: '' },
            { icon: AlertTriangle, title: 'Dhundh ke Laaye jo Bank Chhupata Hai', desc: 'Galat overdue balance, active dispute flags, aur woh defaults jo score ko kam kar rahe hain sab highlight.', theme: 'red-theme' },
            { icon: CheckCircle2, title: 'Score Badhane ka Game Plan', desc: 'Step-by-step checklist + month-by-month timeline. Sab mapped out.', theme: 'green-theme' },
            { icon: TrendingUp, title: 'Score Simulator', desc: 'Defaults clear karoge toh score kitna badhega? Slide karke dekho real-time.', theme: 'purple-theme' },
            { icon: Lock, title: 'Tera Data Safe Hai', desc: 'Report sirf memory mein process hoti hai. Server pe store nahi hoti.', theme: '' },
            { icon: Globe, title: '11 Bhasha Mein Samjhao', desc: 'Hindi, Bengali, Telugu, Marathi, Tamil. Tera score, teri bhasha mein samjho.', theme: 'green-theme' },
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

      {/* How It Works */}
      <section className="how-section" aria-labelledby="how-heading">
        <h2 id="how-heading" className="section-title">Kaise Kaam Karta Hai?</h2>
        <div className="how-steps">
          <div className="how-step">
            <div className="how-step-num">1</div>
            <h3>Report Upload Karo</h3>
            <p>Apni CIBIL/Equifax/CRIF report PDF upload karo. 10MB se zyada nahi honi chahiye.</p>
          </div>
          <div className="how-step">
            <div className="how-step-num">2</div>
            <h3>AI Analysis</h3>
            <p>Humari AI report padhti hai, negative entries dhundhti hai, aur recovery plan banati hai.</p>
          </div>
          <div className="how-step">
            <div className="how-step-num">3</div>
            <h3>Roadmap Download Karo</h3>
            <p>Step-by-step action plan + ready-to-send dispute letters. Apni bhasha mein.</p>
          </div>
        </div>
      </section>

      {/* Pricing Grid */}
      <section className="pricing-section" aria-labelledby="pricing-heading">
        <h2 id="pricing-heading" className="section-title">Kya Chalu Karna Hai? Bas Ek Click.</h2>
        <p className="section-subtitle">Tera score kya keh raha hai? Jan le, phir decide kar.</p>
        <div className="pricing-grid" role="list">
          {['Starter', 'Follow-up', 'Recovery'].map((plan) => {
            const isPopular = plan === 'Follow-up';
            const price = PLAN_PRICES[plan];
            const features = PLAN_FEATURES[plan];
            const packKey = plan === 'Starter' ? 'starterPack' : plan === 'Follow-up' ? 'followupPack' : 'recoveryPack';

            return (
              <div key={plan} className={`pricing-card ${isPopular ? 'popular' : ''}`} role="listitem">
                {isPopular && <div className="popular-tag" aria-label="Most popular plan">🔥 Logon ka Favourite</div>}
                <h3 className="plan-name">{t(packKey) || plan}</h3>
                <div className="plan-price-wrapper" aria-label={`₹${price} one-time`}>
                  <span className="plan-currency">₹</span>
                  <span className="plan-price">{price}</span>
                  <span className="plan-price-subtitle">one-time</span>
                </div>
                <ul className="pricing-features" role="list">
                  {features.map((fk, i) => (
                    <li key={i} className="pricing-feature-item">
                      <CheckCircle2 size={16} aria-hidden="true" />
                      <span>{t(fk) || fk}</span>
                    </li>
                  ))}
                </ul>
                <button
                  className={`btn ${isPopular ? 'btn-primary' : 'btn-secondary'} pricing-btn`}
                  onClick={() => selectPlan(plan)}
                  aria-label={`Choose ${plan} — ₹${price}`}
                >
                  {plan === 'Starter' ? 'Basics se Shuru Karo' : plan === 'Follow-up' ? 'Full Package Lo' : 'Full Recovery'} — ₹{price}
                </button>
              </div>
            );
          })}
        </div>
      </section>

      {/* FAQ */}
      <section className="faq-section" aria-labelledby="faq-heading">
        <h2 id="faq-heading" className="section-title">Aksar Poochhe Jaane Wale Sawal</h2>
        <div className="faq-list">
          <details className="faq-item">
            <summary>Kya mera data safe hai?</summary>
            <p>Haan. Report sirf aapke browser mein process hoti hai. Server pe kuch bhi store nahi hota. Analysis ke baad temp files delete ho jaate hain.</p>
          </details>
          <details className="faq-item">
            <summary>Kaunsi reports accept hoti hain?</summary>
            <p>CIBIL, Equifax, Experian, CRIF — sab accepted hain. PDF format mein upload karna hai. Scanned reports ke liye OCR available hai.</p>
          </details>
          <details className="faq-item">
            <summary>Kitna time lagta hai?</summary>
            <p>Usually 30-60 seconds. Report size aur complexity pe depend karta hai.</p>
          </details>
          <details className="faq-item">
            <summary>Refund policy kya hai?</summary>
            <p>Agar report process nahi hoti ya analysis galat aata hai, toh full refund. No questions asked.</p>
          </details>
        </div>
      </section>
    </div>
  );
}
