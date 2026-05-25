# CLYR v2 — Credit Report Clarity

**India's friendliest credit report analysis tool.**

Upload your CIBIL/Equifax/CRIF report PDF. Get a plain-language breakdown in 11 Indian languages, a step-by-step recovery roadmap, and ready-to-send dispute letters.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLYR v2                              │
├──────────────────┬──────────────────────────────────────────┤
│   Frontend       │   Backend                                 │
│   React 19       │   Python 3.11 + FastAPI                  │
│   Vite           │   Supabase (PostgreSQL + Auth)           │
│   Vanilla CSS    │   OpenRouter (LLM)                       │
│   PWA            │   Razorpay (Payments)                    │
│                  │   Resend (Emails)                         │
│                  │   Sentry (Monitoring)                     │
└──────────────────┴──────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Node 20+
- Python 3.11+
- Supabase project
- OpenRouter API key
- Razorpay account (test or live)

### 1. Clone & Configure
```bash
cp backend/.env-v2.example backend/.env
cp frontend/.env-v2.example frontend/.env.local
# Fill in your API keys
```

### 2. Database Setup
Create a Supabase project and run the schema in `docs/plans/v2-redesign.md`.

### 3. Backend
```bash
cd backend
python -m venv .venv
source .venv/activate  # Windows: .venv\Scripts\activate
pip install -r requirements-v2.txt
uvicorn app.main:app --reload
```

### 4. Frontend
```bash
cd frontend
npm install
npm run dev
```

### 5. Build for Production
```bash
cd frontend && npm run build
cd backend && docker-compose up -d
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/reports/upload` | Upload PDF, analyze with LLM |
| GET | `/api/reports` | List user's reports |
| GET | `/api/reports/:id` | Get report details |
| GET | `/api/pdf/download/:id` | Download PDF (requires payment) |
| POST | `/api/payments/create-order` | Create Razorpay order |
| POST | `/api/payments/verify` | Verify payment |
| POST | `/api/payments/webhook` | Razorpay webhook |
| POST | `/api/waitlist` | Join waitlist |
| GET | `/api/admin/dashboard` | Admin stats |
| GET | `/api/dsa/stats` | DSA partner stats |
| GET | `/api/dsa/referral-link` | Get/create referral link |

## User Flow

1. **Landing** → User sees value proposition, selects plan
2. **Upload** → Drag-and-drop PDF upload (max 10MB)
3. **Analysis** → LLM analyzes report in 30-60 seconds
4. **Dashboard** → Free preview: score, issues, action steps, timeline, simulator
5. **Payment** → Click download → Razorpay checkout
6. **Download** → Full PDF with dispute letters + recovery roadmap

## Tech Decisions

- **Supabase Auth** over custom JWT — battle-tested, email verification, SSO
- **PostgreSQL** over SQLite — concurrent access, Row Level Security, Supabase ecosystem
- **OpenRouter** over direct OpenAI — model flexibility, cost optimization
- **Vanilla CSS** over Tailwind — full control, no build step, smaller bundle
- **Resend** over SendGrid — modern API, better DX, generous free tier

## Testing

```bash
cd backend
pytest tests/ -v
```

## Deployment

```bash
docker-compose up -d
```

Single container, multi-stage build. Frontend served as static files from FastAPI.

## License

MIT
