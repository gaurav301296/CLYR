# ADR-001: Technology Stack Selection

## Status: Accepted

## Date: 2026-05-21

## Context

CLYR needs a tech stack that supports:
1. PDF text extraction from complex Indian credit bureau reports
2. AI/LLM-powered analysis of unstructured financial text
3. Multi-language PDF generation (11 Indian languages)
4. Fast iteration for a 0-to-1 product
5. Low infrastructure cost (₹0 startup budget)

## Decision

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Backend | Python + FastAPI | Best PDF processing ecosystem (pdfplumber), native OpenAI SDK, async support, auto OpenAPI docs |
| Frontend | React 19 + Vite | Fastest dev server, smallest bundle, largest talent pool |
| Database | PostgreSQL (Supabase) | Free tier, Row Level Security, built-in auth, realtime subscriptions |
| Auth | Supabase Auth | Free tier, email+OTP, JWT-based, no custom auth code needed |
| Payments | Razorpay | Indian-first, lowest fees (2%), excellent API, test mode |
| Analytics | PostHog | Free tier 1M events/mo, self-hostable, product analytics + session replay |
| AI | OpenAI gpt-4o-mini | Best price/performance for structured JSON output, 128K context |
| CSS | Vanilla CSS | No design system dependency, full control, zero bundle cost |
| Deployment | Docker + docker-compose | Single-command deploy, works on any VPS |

## Consequences

**Positive:**
- Zero licensing cost for entire stack
- Single language (Python/JS) for full stack
- Supabase eliminates need for custom auth service
- FastAPI auto-generates API docs

**Negative:**
- Vendor lock-in to Supabase (mitigated: PostgreSQL is portable)
- OpenAI API costs scale with usage (mitigated: gpt-4o-mini is $0.15/1M tokens)
- No type safety on frontend (mitigated: Pydantic validates all backend inputs)

## Alternatives Considered

- **Django instead of FastAPI:** Too heavy for API-only service
- **Next.js instead of Vite+React:** Overkill for SPA, higher hosting cost
- **Firebase instead of Supabase:** No SQL, worse pricing, Google lock-in
- **Stripe instead of Razorpay:** Doesn't support UPI natively, higher fees in India
- **Claude API instead of OpenAI:** More expensive, no significant quality gain for this use case
