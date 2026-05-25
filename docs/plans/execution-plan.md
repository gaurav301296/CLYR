# CLYR v2 — Execution Plan (Updated May 25, 2026)

## Already Fixed This Session
- [x] font_manager.py ssrf import → inline URL allowlist
- [x] useAppState t() → real i18n translations
- [x] Header Sign In button → opens AuthModal
- [x] LLM service lazy init + regex fallback
- [x] Waitlist table updated_at column
- [x] Backend dependencies installed (Python 3.12 .venv)
- [x] Frontend builds cleanly
- [x] GitHub repo created + pushed (gaurav301296/CLYR)

## PHASE 0: LOGO + BRAND ASSETS (Do Now — 30 min)

### 0.1 Logo Integration
- Source: `C:\Users\shiva\Downloads\logo CLYR.png` (1536×1024)
- Copy to `frontend/public/logo-clyr.png`
- Generate favicon set (ico, 16x16, 32x32, apple-touch-icon)
- Create OG image (1200×630)
- Update index.html favicon links

### 0.2 Design System Alignment
- Extract dominant colors from logo
- Update CSS `:root` variables if logo colors differ from current gold+purple
- Current: --primary: #F59E0B (gold), --accent: #8B5CF6 (purple), --bg: #0F172A

## PHASE 1: CRITICAL BUG FIXES (Do Next — 2-3 hours)

### 1.1 Auth Flow: Anonymous Upload → Pay to Download
**Backend:**
- `POST /api/reports/upload` — already uses get_optional_user ✓
- `GET /api/pdf/download/:id` — requires auth, change to token-based access
- `POST /api/payments/create-order` — already has anonymous route ✓
- Add webhook: `POST /api/payments/webhook`
- Fix order lookup by razorpay_order_id (not local id)

**Frontend:**
- Remove auth gate from upload flow
- After payment success → prompt "Create account to save reports"
- "Shuru Karo" on landing → goes directly to upload

### 1.2 JWT Secret Persistence
- File: `backend/app/services/auth_service.py` line 77
- Change: stable dev secret, require in production
- Add JWT_SECRET to .env

### 1.3 Password Hashing: SHA-256 → bcrypt
- Install bcrypt, replace _hash_password and _verify_password
- Add migration for existing users (re-hash on next login)

### 1.4 Custom JWT → PyJWT
- Install PyJWT, replace custom token creation/verification
- More secure, standard library

### 1.5 Remove Fake Social Proof
- Remove hardcoded "5,000+ reports", "4.8★", "+75 avg score boost"
- Replace with real data or remove entirely

### 1.6 Deduplicate API_BASE
- AuthContext.jsx, AuthModal.jsx, PaymentPage.jsx all have hardcoded API_BASE
- Route everything through apiFetch/apiUpload from client.js

### 1.7 Input Validation
- Password: min 8 chars, 1 uppercase + 1 number
- File: verify PDF magic bytes (not just extension)
- Language: whitelist against supported languages

## PHASE 2: HYPEROFRAMES VIDEO CONTENT (2-3 hours)

### 2.1 Product Explainer (15-30 sec, 9:16 vertical)
- Instagram Reels / YouTube Shorts / TikTok
- "CIBIL score kya hai? → Report upload → AI analysis → Score badhao"
- Dark bg, gold text reveals, GSAP animations

### 2.2 Feature Showcase (30-60 sec, 16:9 horizontal)
- YouTube / Website hero background
- Animated walkthrough of score gauge, issues, action plan

### 2.3 Social Media Teaser (6-10 sec, 1:1 square)
- Instagram post / WhatsApp status
- Quick logo animation + tagline

## PHASE 3: EMAIL SYSTEM (1 hour)

### 3.1 Resend Integration
- Welcome email after signup
- Payment receipt after Razorpay success
- Report ready notification
- Password reset

### 3.2 Email Templates
- Dark theme matching CLYR brand
- Hinglish copy
- Responsive HTML

## PHASE 4: FRONTEND POLISH (2-3 hours)

### 4.1 Loading Skeletons
- Dashboard skeleton: score gauge + issue card placeholders
- Upload skeleton: drag-zone pulse
- Reports skeleton: table row placeholders

### 4.2 Scroll Animations
- IntersectionObserver-based reveal
- Feature cards, pricing cards, how-it-works steps

### 4.3 Micro-interactions
- Button hover: scale + glow
- Card hover: border transition + lift
- Score gauge: animated count-up
- Checklist: strikethrough animation

### 4.4 Mobile Responsiveness Audit
- Pricing grid: 3-col → 1-col
- Dashboard: sidebar → top section
- Touch targets ≥44px

### 4.5 Error Boundary
- Already exists (ErrorBoundary.jsx) but not used in App.jsx
- Wrap page content, show Hinglish error + "Try again"

## PHASE 5: BACKEND HARDENING (1 hour)

### 5.1 Rate Limiting
- Auth: 5/min, Upload: 10/min, General: 60/min
- Already partially implemented, just tighten

### 5.2 Health Check Enhancement
- Return DB connectivity, LLM service status, uptime

### 5.3 CORS Production Config
- Restrict in production (no localhost)
- Add HSTS, CSP headers

## PHASE 6: SEO + CONTENT (1-2 hours)

### 6.1 Content Pages
- CIBIL Guide: "CIBIL Score Kya Hai?"
- Dispute Guide: "CIBIL Dispute Kaise Karein?"
- Expanded FAQ page

### 6.2 Dynamic Meta Tags
- React Helmet for blog posts, guides, pricing
- Structured data (FAQ schema, Product schema)

### 6.3 Sitemap
- Generate sitemap.xml for Google Search Console

## PHASE 7: DEPLOYMENT PREP (1 hour)

### 7.1 Production .env Template
- All required variables documented
- Docker multi-stage build optimization

### 7.2 CI/CD
- GitHub Actions already pushed ✓
- Verify it runs on next push

### 7.3 Monitoring
- Sentry DSN (already integrated)
- Uptime monitoring
- Error alerting to Telegram/WhatsApp

## EXECUTION ORDER

| Order | Task | Time | Status |
|-------|------|------|--------|
| 1 | Logo integration | 30m | PENDING |
| 2 | Auth flow fix (anonymous → pay) | 1h | PENDING |
| 3 | JWT secret persistence | 15m | PENDING |
| 4 | bcrypt password hashing | 30m | PENDING |
| 5 | PyJWT | 30m | PENDING |
| 6 | Remove fake social proof | 15m | PENDING |
| 7 | Deduplicate API_BASE | 30m | PENDING |
| 8 | Input validation | 30m | PENDING |
| 9 | HyperFrames videos | 2-3h | PENDING |
| 10 | Email system | 1h | PENDING |
| 11 | Frontend polish | 2-3h | PENDING |
| 12 | Backend hardening | 1h | PENDING |
| 13 | SEO content | 1-2h | PENDING |
| 14 | Deployment prep | 1h | PENDING |

Total estimated time: ~16-20 hours
