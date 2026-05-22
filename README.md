# Credit Report Clarity (CLYR)

A premium, decision-driven credit wellness and report clarity tool. It parses complex credit reports (PDFs), identifies defaults and negative marks, and produces an actionable, plain-English/Hinglish roadmap for score recovery.

## Getting Started

### Backend (Python FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   Source .venv/Scripts/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend (React + Vite)

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the dev server:
   ```bash
   npm run dev
   ```
