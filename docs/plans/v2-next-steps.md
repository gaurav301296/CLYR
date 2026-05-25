# CLYR v2 — Detailed Next Steps Plan

> Created: 2026-07-15
> Status: Active
> Author: OWL (proactive technical partner)

---

## CURRENT STATE SNAPSHOT

**What works:**
- Full-stack app: FastAPI + React 19 + Vite
- PDF upload → LLM analysis (OpenRouter) → Dashboard display
- SQLite database with reports, orders, users, DSA leads
- Custom JWT auth (signup/login/logout)
- Razorpay payment integration (create-order + verify)
- Score simulator with utilization slider + issue checkboxes
- 11 Indian language support in LLM prompts
- PDF generation (watermarked preview + full download)
- DSA partner portal (stats, leads, referral links)
- Admin dashboard (basic)
- PWA manifest, SEO meta tags, Schema.org markup
- 1541-line CSS design system (dark theme, gold + purple accent)

**What's broken / incomplete:**
- Payment flow requires auth BEFORE analysis (should be: analyze free → pay to download)
- JWT secret random on every restart (tokens invalidate)
- SHA-256 password hashing (not bcrypt)
- Custom JWT (not PyJWT)
- Fake social proof numbers on landing page
- No email verification
- No email service (welcome, receipt, report-ready)
- `t()` function is a pass-through (no real i18n — just returns key names)
- Header logo references `/logo-clyr.png` which doesn't exist in public/
- No error boundary component used in App.jsx (imported but not rendered)
- Mobile menu CSS likely incomplete (referenced but not fully styled)
- No loading skeleton components
- Backend: `payment/create-order` requires auth (blocks anonymous flow)
- Backend: order lookup uses local `id` not `razorpay_order_id`
- Backend: no webhook endpoint for Razorpay async confirmation
- Frontend: `useAppState` `t()` is identity function — all translation keys show as raw strings
- Frontend: AuthModal has `API_BASE` hardcoded (duplicated from config)
- Frontend: PaymentPage has `API_BASE` hardcoded (duplicated)
- Frontend: AuthContext has `API_BASE` hardcoded (duplicated)

---

## PHASE 0: LOGO + BRAND ASSET INTEGRATION

### 0.1 — Logo Analysis & Integration
The logo file is at `C:\Users\shiva\Downloads\logo CLYR.png` (1536×1024 PNG).

**Actions:**
1. Copy logo to `frontend/public/logo-clyr.png` (the path Header.jsx already references)
2. Create `frontend/public/logo-clyr.svg` version if possible (sharper at all sizes)
3. Generate favicon set: `favicon.ico`, `favicon-16x16.png`, `favicon-32x32.png`, `apple-touch-icon.png`
4. Update `index.html` favicon link to point to new assets
5. Add Open Graph image: `frontend/public/og-image.png` (1200×630) — branded CLYR card

### 0.2 — Brand Design System Update
Current colors: `--primary: #F59E0B` (gold), `--accent: #8B5CF6` (purple), `--bg: #0F172A` (dark slate)

**Decision needed:** Does the logo's color palette match the current gold+purple? If the logo uses different primary colors, update the CSS `:root` variables to match. The logo MUST drive the design system, not the other way around.

**Actions:**
1. Extract dominant colors from logo
2. Update CSS custom properties to match logo palette
3. Ensure gradient combinations (primary→accent) still look premium
4. Update button gradients, glow effects, and brand-name gradient to match

---

## PHASE 1: CRITICAL BUG FIXES (Do First — 1-2 Days)

### 1.1 — Fix Auth Flow: Anonymous Analysis → Pay to Download
**Current:** User must sign in before uploading. Payment requires auth.
**Target:** Anyone uploads → gets free preview → pays to download full PDF → optionally creates account after payment.

**Backend changes:**
```
backend/app/routes/reports.py:
  - POST /api/reports/upload: Already uses get_optional_user (GOOD)
  - GET /api/pdf/download/:id: Requires auth → change to token-based or session-based
  - Add: POST /api/payments/create-order-anonymous (no auth, returns order)
  - Add: POST /api/payments/webhook (Razorpay async confirmation)
  - Fix: Order lookup by razorpay_order_id (not local id)
```

**Frontend changes:**
```
frontend/src/hooks/useAppState.js:
  - Remove auth gate from upload flow
  - Add: payment flow works without login
  - After payment success: prompt "Create account to save your reports"

frontend/src/pages/LandingPage.jsx:
  - "Shuru Karo" button → goes directly to upload (not waitlist for logged-out users)
  - Waitlist only shown if no plan selected
```

### 1.2 — Fix JWT Secret Persistence
**File:** `backend/app/services/auth_service.py`
```python
# BEFORE (broken):
JWT_SECRET = os.environ.get("JWT_SECRET", secrets.token_hex(32))

# AFTER (fixed):
JWT_SECRET = os.environ.get("JWT_SECRET")
if not JWT_SECRET:
    if os.getenv("ENVIRONMENT") == "production":
        raise RuntimeError("JWT_SECRET must be set in production")
    JWT_SECRET = "dev-only-secret-change-in-production"  # Stable in dev
```

### 1.3 — Fix Password Hashing: SHA-256 → bcrypt
**File:** `backend/app/services/auth_service.py`
```python
# Add to requirements.txt: bcrypt==4.2.0
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())
```

### 1.4 — Fix Custom JWT → PyJWT
**File:** `backend/app/services/auth_service.py`
```python
# Add to requirements.txt: PyJWT==2.10.0
import jwt

def create_token(payload: dict, secret: str, expires_hours: int = 24) -> str:
    payload["exp"] = datetime.utcnow() + timedelta(hours=expires_hours)
    return jwt.encode(payload, secret, algorithm="HS256")

def decode_token(token: str, secret: str) -> dict:
    return jwt.decode(token, secret, algorithms=["HS256"])
```

### 1.5 — Remove Fake Social Proof
**File:** `frontend/src/pages/LandingPage.jsx`
- Remove any hardcoded "5,000+ reports", "4.8★", "+75 avg score boost"
- Replace with real data from API (if available) or remove entirely
- Trust bar should only show verifiable claims: "100% Encrypted", "Data Store Nahi Hota", "11 Bhasha Mein"

### 1.6 — Fix Translation System
**Current:** `t()` is `(key) => key` — returns raw key names
**Fix:** Implement real i18n with the existing translation key structure.

```
frontend/src/i18n/translations.js:
  - Already has structure (check file)
  - Connect to useAppState t() function
  - Fallback to English if translation missing
```

### 1.7 — Fix Logo Path
**File:** `frontend/src/components/Header.jsx`
```javascript
// BEFORE:
const LOGO_PATH = '/logo-clyr.png';

// AFTER: Use import for Vite bundling
import logoSrc from '../../public/logo-clyr.png';
// Or ensure file exists at frontend/public/logo-clyr.png
```

### 1.8 — Deduplicate API_BASE
Create a single source of truth. Files with hardcoded API_BASE:
- `frontend/src/api/client.js` ✓ (already uses config)
- `frontend/src/context/AuthContext.jsx` ✗ (hardcoded)
- `frontend/src/components/AuthModal.jsx` ✗ (hardcoded)
- `frontend/src/pages/PaymentPage.jsx` ✗ (hardcoded)

**Fix:** All API calls should go through `apiFetch()` / `apiUpload()` from `client.js`.

---

## PHASE 2: HYPERFRAMES VIDEO CONTENT (2-3 Days)

HyperFrames v0.6.42 is installed and available. Use it to create premium video content for CLYR marketing.

### 2.1 — Product Explainer Video (15-30 sec, 9:16 vertical)
**Purpose:** Instagram Reels / YouTube Shorts / TikTok
**Content:** "CIBIL score kya hai? → Report upload karo → AI analysis → Score badhao"
**Style:** Dark background (matching CLYR design system), gold text reveals, GSAP animations

**Structure:**
```
0.0-0.5s: Black screen
0.5-2.0s: "Tera CIBIL score kya keh raha hai?" — text fade-in
2.0-3.5s: "Report upload karo" — slide up animation
3.5-5.0s: "AI analysis karega" — typewriter effect
5.0-7.0s: "Score kaise badhayein — samjhayega" — staggered text
7.0-9.0s: CLYR logo reveal + "₹499 se shuru karo" — scale + glow
```

**Implementation:**
```bash
cd C:/Users/shiva/Downloads/CLYR
npx hyperframes init clyr-explainer
# Edit index.html with CLYR design system colors
# Add GSAP timeline with paused: true
npx hyperframes render --output clyr-explainer-vertical.mp4
```

### 2.2 — Feature Showcase Video (30-60 sec, 16:9 horizontal)
**Purpose:** YouTube / Website hero background
**Content:** Animated walkthrough of CLYR features — score gauge, issues list, action plan, PDF download

### 2.3 — Social Media Teaser (6-10 sec, 1:1 square)
**Purpose:** Instagram post / WhatsApp status
**Content:** Quick CLYR logo animation + tagline

### 2.4 — Testimonial/Proof Video Template (9:16)
**Purpose:** User testimonials (to be filled with real content later)
**Template:** Quote animation + user avatar placeholder + CLYR branding

### HyperFrames Technical Requirements:
- All compositions: `data-width="1080" data-height="1920"` for 9:16
- GSAP timelines MUST use `{ paused: true }`
- All animated elements need `class="clip"`
- Use CLYR colors: `#0F172A` bg, `#F59E0B` primary, `#8B5CF6` accent
- Font: IBM Plex Sans (match web app)
- Output: `renders/` directory, named descriptively

---

## PHASE 3: EMAIL SYSTEM (1 Day)

### 3.1 — Resend Email Integration
**Backend:** `backend/app/services/email_service.py` (already exists from uncommitted changes)

**Emails to implement:**
1. **Welcome email** — After signup
2. **Payment receipt** — After successful Razorpay payment
3. **Report ready notification** — After LLM analysis completes (if async)
4. **Password reset** — Forgot password flow

**Email design:** Dark theme matching CLYR brand, gold accents, Hinglish copy.

### 3.2 — Email Templates
```
backend/app/templates/emails/
  ├── welcome.html
  ├── payment_receipt.html
  ├── report_ready.html
  └── password_reset.html
```

---

## PHASE 4: FRONTEND POLISH (2-3 Days)

### 4.1 — Loading States & Skeletons
**Current:** Basic spinner text
**Upgrade:** Skeleton screens matching the layout of each page
- Dashboard skeleton: score gauge placeholder + issue card placeholders
- Upload skeleton: drag-zone pulse animation
- Reports skeleton: table row placeholders

### 4.2 — Scroll-Triggered Animations
Add IntersectionObserver-based reveal animations (matching the Bajrangi site pattern):
```css
.reveal {
  opacity: 0;
  transform: translateY(24px);
  transition: opacity 0.6s ease-out, transform 0.6s ease-out;
}
.reveal.visible {
  opacity: 1;
  transform: translateY(0);
}
```

Apply to:
- Feature cards (staggered reveal)
- Pricing cards (staggered reveal)
- How-it-works steps (left-to-right reveal)
- FAQ items (fade-in)

### 4.3 — Micro-interactions
- Button hover: scale(1.02) + glow shadow
- Card hover: border-color transition + subtle lift
- Score gauge: animated count-up on load
- Checklist: strikethrough animation on check
- Simulator: smooth score number transition

### 4.4 — Mobile Responsiveness Audit
**Current CSS has media queries but needs verification:**
- Pricing grid: 3-col → 1-col on mobile
- Features grid: 3-col → 2-col → 1-col
- Dashboard: sidebar → top section on mobile
- Header: nav → hamburger menu (already implemented)
- Upload zone: full width on mobile
- Touch targets: all ≥44px (already in CSS)

### 4.5 — Error Boundary
**Current:** ErrorBoundary.jsx exists but not used in App.jsx
**Fix:** Wrap page content in ErrorBoundary, show friendly Hinglish error message with "Try again" button.

### 4.6 — 404 Page Enhancement
**Current:** Basic 404 with Hinglish text
**Upgrade:** Add animated illustration, search suggestions, popular links.

---

## PHASE 5: BACKEND HARDENING (1-2 Days)

### 5.1 — Rate Limiting on Auth Endpoints
**File:** `backend/app/middleware/rate_limit.py`
```python
# Stricter limits for auth routes:
AUTH_LIMIT = 5  # per minute
UPLOAD_LIMIT = 10  # per minute
GENERAL_LIMIT = 60  # per minute
```

### 5.2 — Input Validation
- Password: min 8 chars, require 1 uppercase + 1 number
- Email: proper validation (already using Pydantic EmailStr)
- File: verify PDF magic bytes (not just extension)
- Language: whitelist against supported languages only

### 5.3 — Razorpay Webhook
**Add:** `POST /api/payments/webhook`
- Verify webhook signature
- Update order status asynchronously
- Handle payment.failed events

### 5.4 — Health Check Endpoint
**Current:** `GET /api/health` (exists)
**Enhance:** Return DB connectivity status, LLM service status, uptime.

### 5.5 — CORS & Security Headers
**Current:** Basic CORS configured
**Enhance:**
- Restrict CORS in production (no localhost)
- Add HSTS header
- Add Content-Security-Policy for frontend

---

## PHASE 6: SEO + CONTENT PAGES (1-2 Days)

### 6.1 — Blog/SEO Content Pages
**Purpose:** Organic traffic for "CIBIL score improve kaise karein" etc.

**Pages to create:**
```
frontend/src/pages/
  ├── BlogPage.jsx          # Blog listing
  ├── BlogPost.jsx          # Individual post
  ├── CibilGuidePage.jsx    # "CIBIL Score Kya Hai?" evergreen guide
  ├── DisputeGuidePage.jsx  # "CIBIL Dispute Kaise Karein?" guide
  └── FaqPage.jsx           # Expanded FAQ (separate from landing page FAQ)
```

### 6.2 — Dynamic Meta Tags
Add React Helmet or manual meta tag management for:
- Blog posts (title, description, OG image)
- Guide pages (structured data for FAQ schema)
- Pricing page (Product schema)

### 6.3 — Sitemap
Generate `sitemap.xml` with all pages for Google Search Console.

---

## PHASE 7: ADMIN DASHBOARD ENHANCEMENT (1 Day)

### 7.1 — Current: Basic stats + tables
### 7.2 — Enhanced:
- Revenue chart (daily/weekly/monthly)
- User growth chart
- Report processing stats (success rate, avg time)
- Waitlist conversion funnel
- DSA partner leaderboard
- Export to CSV functionality

---

## PHASE 8: DEPLOYMENT PREP (1 Day)

### 8.1 — Environment Configuration
- Production `.env` template
- Docker multi-stage build optimization
- Health check for container orchestration

### 8.2 — CI/CD
- GitHub Actions: run tests on PR
- Auto-deploy to staging on merge to `main`
- Production deploy on tag

### 8.3 — Monitoring
- Sentry (already integrated, just needs DSN)
- Uptime monitoring (cron job or external service)
- Error alerting to Telegram/WhatsApp

---

## EXECUTION ORDER (Priority)

| Priority | Phase | Effort | Impact |
|----------|-------|--------|--------|
| **P0** | Phase 1: Critical Bug Fixes | 1-2 days | Unblocks everything |
| **P0** | Phase 0: Logo Integration | 0.5 day | Brand consistency |
| **P1** | Phase 4: Frontend Polish | 2-3 days | User experience |
| **P1** | Phase 2: HyperFrames Videos | 2-3 days | Marketing content |
| **P2** | Phase 3: Email System | 1 day | User communication |
| **P2** | Phase 5: Backend Hardening | 1-2 days | Security |
| **P3** | Phase 6: SEO Content | 1-2 days | Organic growth |
| **P3** | Phase 7: Admin Enhancement | 1 day | Operations |
| **P4** | Phase 8: Deployment Prep | 1 day | Launch readiness |

---

## IMMEDIATE NEXT ACTIONS (What I'll do first)

1. **Copy logo** to `frontend/public/` and verify it loads
2. **Fix the auth flow** — anonymous upload → pay to download
3. **Fix JWT secret** persistence
4. **Replace SHA-256** with bcrypt
5. **Replace custom JWT** with PyJWT
6. **Fix translation system** — connect real i18n
7. **Remove fake social proof**
8. **Create HyperFrames** product explainer video
9. **Add scroll animations** to landing page
10. **Implement email service** with Resend

---

## NOTES

- The codebase is already well-structured. Most fixes are targeted, not architectural.
- The design system (CSS) is excellent — 1541 lines of thoughtful dark-theme work. Don't rewrite it.
- The LLM service is solid — retry logic, caching, fallback parsing all in place.
- The biggest gap is the auth/payment flow architecture. Fix that first.
- HyperFrames is installed and ready. Use it for marketing videos — this is a competitive advantage.
- Logo colors should drive any design system updates. Check logo first before changing colors.
