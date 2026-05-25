# CLYR v2 — Complete Redesign Plan

## Executive Summary

CLYR is a credit report analysis platform for the Indian market. The current codebase (v1)
is a functional MVP with: FastAPI backend, React frontend, PDF parsing via pdfplumber,
LLM-powered analysis via OpenRouter, Razorpay payments, Supabase auth, and 11 Indian
language support with ReportLab PDF generation.

After reading every source file, I've identified critical bugs, architectural flaws,
security issues, and missing product features. This plan addresses all of them.

---

## PART 1: BUGS FOUND (Must Fix)

### Critical Bugs

1. **Payment flow broken for anonymous users**
   - `POST /payment/create-order` requires `get_current_user` (authenticated)
   - But LandingPage has NO authentication flow — users arrive, pick a plan, and hit a pay wall
   - They can't create an account from the landing page flow either (auth modal exists but is disconnected from payment)
   - FIX: Allow anonymous payment,THEN prompt account creation after payment succeeds

2. **JWT secret is random on every startup**
   - `auth_service.py` line 77: `JWT_SECRET = os.environ.get("JWT_SECRET", secrets.token_hex(32))`
   - Every server restart generates a new secret → all existing tokens become invalid
   - FIX: Require JWT_SECRET in production, fail to start without it

3. **No password strength validation**
   - `signup_user` accepts any password including "123456"
   - FIX: Add minimum length (8 chars), complexity requirements

4. **Refresh tokens never cleaned up automatically**
   - `cleanup_expired_tokens()` exists but is never called
   - Tokens accumulate forever in the DB
   - FIX: Add periodic cleanup via background task or cron

5. **Order lookup by razorpay_order_id is fragile**
   - `update_order_payment` uses `WHERE id=?` but the order was created with a local `order_id`, NOT the `razorpay_order_id`
   - The local id and razorpay id are DIFFERENT values
   - FIX: Look up orders by razorpay_order_id, not local id

6. **Hardcoded fake social proof**
   - Landing page shows "5,000+ reports", "4.8★", "+75 avg score boost"
   - These are lies for a brand-new product. Users will trust nothing.
   - FIX: Remove or connect to real analytics

7. **No email verification on signup**
   - Anyone can sign up with any email. No confirmation sent.
   - FIX: Add email verification flow (or at minimum, use OTP)

### Security Issues

8. **Password hashing is SHA-256, not bcrypt**
   - `auth_service.py`: `hashlib.sha256((salt + password).encode())`
   - SHA-256 is NOT a password hashing algorithm. It's fast = brute-forceable.
   - FIX: Use bcrypt or argon2

9. **Custom JWT implementation is not secure**
   - Hand-rolled JWT with `base64` + `sha256` is vulnerable to algorithm confusion attacks
   - FIX: Use a proper JWT library (PyJWT or python-jose)

10. **Supabase auth is configured but never used**
    - .env has Supabase keys but the app uses local SQLite auth
    - Supabase client is imported but never initialized
    - FIX: Either use Supabase auth properly OR remove the dead config

11. **SSRF protection exists but is never used**
    - `ssrf.py` is written but never called from any route
    - FIX: Integrate into any outbound request, or remove dead code

12. **Secrets validation is NEVER called**
    - `validate_secrets()` in `secrets.py` is never invoked by `main.py`
    - FIX: Call it at startup

13. **No HTTPS enforcement in production**
    - HSTS header is set, but no redirect from HTTP to HTTPS
    - FIX: Add HTTPS redirect middleware in production

### Functional Issues

14. **Upload endpoint doesn't verify the file actually parsed correctly**
    - If LLM returns empty/nonsensical data, user sees it as success
    - FIX: Validate LLM response quality before saving

15. **Download endpoint doesn't require payment verification**
    - Any authenticated user can generate a PDF without paying
    - FIX: Check order status before allowing PDF generation

16. **Timeline dates are stored as unix timestamps**
    - `created_at` stored as `time.time()` float — works but hard to query
    - FIX: Use ISO 8601 strings for readability

17. **LLM service has no retry logic**
    - If OpenRouter is down, the upload fails with no retry
    - FIX: Add exponential backoff retry (3 attempts)

18. **No rate limiting on auth endpoints**
    - `POST /auth/signup` and `POST /auth/login` are not rate-limited
    - Vulnerable to brute-force attacks
    - FIX: Add stricter rate limits on auth routes

---

## PART 2: MISSING PRODUCT FEATURES

### Must-Have for Launch

1. **Email system** — No welcome email, no payment receipt, no report-ready notification
2. **Admin dashboard** — Owner can't see users, revenue, reports without raw SQL
3. **Proper onboarding** — No guidance on what PDF to upload, what CIBIL report looks like
4. **Progress tracking** — User saves their dashboard state, comes back, sees progress
5. **PDF preview before purchase** — Show a preview/watermarked version before payment
6. **Blog / SEO content** — "How to improve CIBIL score" etc. for organic traffic
7. **Referral program** — Code exists in DB but no UI, no conversion tracking

### Should-Have

8. **WhatsApp notification integration** — Indians use WhatsApp, not email
9. **Report history comparison** — Upload a second report 3 months later, see score change
10. **Dispute letter tracking** — Track which letters were sent, when, response received
11. **Multi-bureau support** — CIBIL, Equifax, Experian, CRIF — different formats
12. **Aadhaar-based identity verification** — For DSA partners
13. **Dark/light mode toggle** — Currently dark only

### Nice-to-Have

14. **Mobile app** — PWA at minimum
15. **PDF OCR support** — Many credit reports are scanned images
16. **Telegram bot** — Upload PDF via Telegram, get analysis
17. **Partner API** — Let CA firms / DSA partners integrate

---

## PART 3: v2 ARCHITECTURE DESIGN

### Design Philosophy

The v1 was built as a prototype — SQLite, custom auth, hand-rolled JWT, mixed concerns.
v2 should be built as a **production-grade business platform**. That means:

1. **PostgreSQL** instead of SQLite (Supabase Postgres — you already pay for it)
2. **Supabase Auth** instead of custom SQLite auth (battle-tested, SSO, email verification)
3. **Proper async** — Use async database drivers, don't block the event loop
4. **Separated concerns** — Auth service, LLM service, Payment service are independent modules
5. **Observability** — Structured logging, health checks, metrics from day one
6. **Security first** — bcrypt, proper JWT, rate limiting, input validation everywhere

### File Structure (v2)

```
CLYR/
├── backend/
│   ├── app/
│   │   ├── main.py              # App entry, middleware, routing
│   │   ├── config.py            # Centralized config with validation
│   │   ├── database.py          # Supabase client + connection management
│   │   ├── models/              # Pydantic models for all requests/responses
│   │   │   ├── auth.py
│   │   │   ├── report.py
│   │   │   ├── payment.py
│   │   │   └── user.py
│   │   ├── routes/              # API route handlers (thin)
│   │   │   ├── auth.py
│   │   │   ├── reports.py
│   │   │   ├── payments.py
│   │   │   ├── admin.py
│   │   │   └── health.py
│   │   ├── services/            # Business logic (thick)
│   │   │   ├── llm_service.py   # LLM analysis with retry + caching
│   │   │   ├── pdf_service.py   # PDF parsing + generation
│   │   │   ├── payment_service.py # Razorpay integration
│   │   │   ├── email_service.py  # Transactional emails
│   │   │   └── analytics_service.py # Internal analytics
│   │   ├── middleware/            # FastAPI middleware
│   │   │   ├── auth.py
│   │   │   ├── rate_limit.py
│   │   │   ├── security_headers.py
│   │   │   └── logging.py
│   │   └── utils/               # Pure utility functions
│   │       ├── sanitization.py
│   │       ├── validators.py
│   │       └── exceptions.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_reports.py
│   │   ├── test_payments.py
│   │   └── test_llm.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── api/                 # API client layer
│   │   │   ├── client.js        # Axios/fetch wrapper with auth
│   │   │   ├── auth.js
│   │   │   ├── reports.js
│   │   │   └── payments.js
│   │   ├── components/          # Reusable UI components
│   │   │   ├── ui/              # Button, Input, Card, Modal, etc.
│   │   │   ├── layout/          # Header, Footer, Sidebar
│   │   │   └── shared/          # LoadingSpinner, ErrorBoundary
│   │   ├── pages/               # Route-level page components
│   │   │   ├── LandingPage.jsx
│   │   │   ├── UploadPage.jsx
│   │   │   ├── DashboardPage.jsx
│   │   │   ├── PaymentPage.jsx
│   │   │   ├── ReportsPage.jsx
│   │   │   ├── ProfilePage.jsx
│   │   │   ├── AdminPage.jsx
│   │   │   └── DsaPortal.jsx
│   │   ├── hooks/               # Custom React hooks
│   │   │   ├── useAuth.js
│   │   │   ├── useReports.js
│   │   │   └── usePayments.js
│   │   ├── context/             # React context providers
│   │   │   ├── AuthContext.jsx
│   │   │   └── AppContext.jsx
│   │   ├── i18n/                # Translations
│   │   │   └── translations.js
│   │   ├── lib/                 # Utility libraries
│   │   │   ├── supabase.js
│   │   │   ├── analytics.js
│   │   │   ├── validation.js
│   │   │   └── logger.js
│   │   ├── styles/              # CSS modules
│   │   │   ├── globals.css
│   │   │   ├── components.css
│   │   │   └── pages.css
│   │   └── config.js            # App configuration
│   ├── public/
│   ├── package.json
│   ├── vite.config.js
│   ├── Dockerfile
│   └── .env.example
├── docs/
│   ├── adr/                     # Architecture Decision Records
│   ├── api/                     # API documentation
│   └── deployment/              # Deployment guides
├── docker-compose.yml
├── Dockerfile                   # Multi-stage production build
├── .env.example
├── .gitignore
└── README.md
```

### Database Schema (v2 — Supabase PostgreSQL)

```sql
-- Use Supabase Auth for users (no custom users table needed)
-- But we extend with a profiles table

CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    avatar_url TEXT DEFAULT '',
    role TEXT DEFAULT 'user' CHECK (role IN ('user', 'dsa', 'admin')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    customer_name TEXT DEFAULT '',
    score INTEGER DEFAULT 0 CHECK (score BETWEEN 300 AND 900),
    language TEXT DEFAULT 'en',
    letter_text TEXT DEFAULT '',
    issues JSONB DEFAULT '[]'::jsonb,
    action_steps JSONB DEFAULT '[]'::jsonb,
    timeline JSONB DEFAULT '[]'::jsonb,
    general_health TEXT DEFAULT '',
    status TEXT DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'failed')),
    pdf_url TEXT DEFAULT '',  -- Supabase Storage URL for generated PDF
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    report_id UUID REFERENCES reports(id) ON DELETE SET NULL,
    plan TEXT NOT NULL CHECK (plan IN ('Starter', 'Follow-up', 'Recovery')),
    amount INTEGER NOT NULL,  -- in paise
    currency TEXT DEFAULT 'INR',
    razorpay_order_id TEXT DEFAULT '',
    razorpay_payment_id TEXT DEFAULT '',
    razorpay_signature TEXT DEFAULT '',
    status TEXT DEFAULT 'created' CHECK (status IN ('created', 'paid', 'failed', 'refunded')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE waitlist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    source TEXT DEFAULT 'landing_page',
    converted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE dsa_leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dsa_user_id UUID REFERENCES auth.users(id),
    client_name TEXT DEFAULT '',
    client_email TEXT DEFAULT '',
    score INTEGER DEFAULT 0,
    plan TEXT DEFAULT 'Starter',
    status TEXT DEFAULT 'Actioned' CHECK (status IN ('Actioned', 'Contacted', 'Converted', 'Paid')),
    commission INTEGER DEFAULT 100,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE dsa_referrals (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id),
    referral_code TEXT UNIQUE NOT NULL,
    referral_link TEXT NOT NULL,
    total_clicks INTEGER DEFAULT 0,
    total_conversions INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_reports_user ON reports(user_id);
CREATE INDEX idx_reports_status ON reports(status);
CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_razorpay ON orders(razorpay_order_id);
CREATE INDEX idx_dsa_leads_user ON dsa_leads(dsa_user_id);
CREATE INDEX idx_waitlist_email ON waitlist(email);

-- Row Level Security (RLS)
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE dsa_leads ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY "Users see own profile" ON profiles FOR ALL USING (auth.uid() = id);
CREATE POLICY "Users see own reports" ON reports FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users see own orders" ON orders FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "DSA sees own leads" ON dsa_leads FOR ALL USING (auth.uid() = dsa_user_id);
```

### API Design (v2)

```
# Health
GET  /api/health

# Auth (Supabase-based)
POST /api/auth/signup          # Email + password → Supabase signup + email verification
POST /api/auth/login           # Email + password → Supabase session
POST /api/auth/logout          # Clear session
POST /api/auth/forgot-password # Send reset email
POST /api/auth/reset-password  # Reset with token
GET  /api/auth/verify-email    # Verify email with token

# Reports
POST /api/reports/upload       # Upload PDF → returns report_id (async processing)
GET  /api/reports              # List user's reports
GET  /api/reports/:id          # Get report details
POST /api/reports/:id/regenerate  # Re-run LLM analysis

# Payments
POST /api/payments/create-order    # Create Razorpay order (works for anonymous too)
POST /api/payments/verify          # Verify payment
POST /api/payments/webhook         # Razorpay webhook for async confirmation
GET  /api/payments/status/:id      # Check payment status

# PDF
GET  /api/pdf/download/:report_id  # Download generated PDF (requires payment)
GET  /api/pdf/preview/:report_id   # Get watermarked preview (free)

# Admin
GET  /api/admin/dashboard          # Dashboard stats
GET  /api/admin/users             # User list
GET  /api/admin/reports           # All reports
GET  /api/admin/orders            # All orders
GET  /api/admin/waitlist          # Waitlist entries

# DSA
GET  /api/dsa/stats               # Partner stats
GET  /api/dsa/leads               # Partner's leads
POST /api/dsa/leads               # Create lead
GET  /api/dsa/referral            # Get/create referral link

# Waitlist
POST /api/waitlist                # Add to waitlist
```

---

## PART 4: IMPLEMENTATION ORDER

### Phase 1: Foundation (Backend)
1. Set up Supabase project + database schema
2. Create config.py with proper env validation
3. Replace custom auth with Supabase Auth
4. Fix all critical bugs (JWT, password hashing, order lookup)
5. Add proper error handling + retry logic

### Phase 2: Core Features (Backend)
6. Rebuild report upload with async processing
7. Rebuild LLM service with retry + caching
8. Rebuild PDF generation (keep the good design, fix parsing)
9. Rebuild payment flow (anonymous → account creation)
10. Add email service (welcome, receipt, report-ready)

### Phase 3: Frontend Rebuild
11. Set up proper API client layer
12. Rebuild auth flow (Supabase SDK)
13. Rebuild landing page (remove fake social proof)
14. Rebuild upload → analysis → dashboard flow
15. Add admin dashboard
16. Add DSA portal

### Phase 4: Polish + Launch
17. Add blog/SEO content pages
18. Add referral system
19. Add analytics dashboard
20. Security audit + penetration testing
21. Performance optimization
22. Deploy to production
