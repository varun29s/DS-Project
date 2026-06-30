# Instagram Clone — 3-service architecture

A simple Instagram clone split into three runnable services:

```
┌────────────┐      ┌──────────────────┐      ┌─────────────────────────┐
│  frontend  │ ───▶ │   backend (API)  │ ───▶ │  recommendsys (ML)      │
│  React/Vite│ HTTP │  FastAPI :8000   │ HTTP │  FastAPI :8001          │
│   :5173    │      │  auth, posts,    │      │  ranks reels per user   │
└────────────┘      │  reels, storage  │      └───────────┬─────────────┘
                    └────────┬─────────┘                  │ reads
                             │ reads/writes               │
                             ▼                            ▼
                         Database (Supabase Postgres, or local SQLite)
```

| Folder | Service | Port | Role |
|--------|---------|------|------|
| [`frontend/`](frontend) | React (Vite) SPA | 5173 | UI |
| [`backend/`](backend) | FastAPI | 8000 | Auth, posts, stories, reels, storage; API gateway |
| [`recommendsys/`](recommendsys) | FastAPI (ML) | 8001 | Reel recommendation engine |

The **frontend** only talks to the **backend**. The backend calls the
**recommendsys** service for `/reels/recommended` and hydrates the ranked IDs
(falling back to a chronological feed if the ML service is down).

## Quick start (local, SQLite — zero external services)

The repo ships with `.env` files preconfigured for a shared local **SQLite** DB,
plus a seed of sample data, so all three run with no Supabase needed.

```bash
./start-all.sh
```

This sets up venvs/deps if needed, seeds the DB, and launches all three:

- Frontend → http://localhost:5173
- Backend docs → http://localhost:8000/docs
- ML service → http://localhost:8001/health

**Demo login:** `demo` / `password123` (also `alice`, `bob`, `carol`, `dave`).
The `demo` account already follows people and has liked reels, so
`/reels` shows personalized suggestions with reasons immediately.

> Local SQLite mode is for testing the app + recommender. **Media uploads need
> Supabase** — to enable them, put real Supabase credentials in `backend/.env`
> and point both `DATABASE_URL`s at your Supabase Postgres URI.

## Run manually (three terminals)

```bash
# 1. ML service
cd recommendsys && python -m venv .venv && source .venv/bin/activate \
  && pip install -r requirements.txt && uvicorn app.main:app --port 8001

# 2. Backend (seed once, then run)
cd backend && python -m venv .venv && source .venv/bin/activate \
  && pip install -r requirements.txt && python -m scripts.seed \
  && uvicorn app.main:app --reload --port 8000

# 3. Frontend
cd frontend && npm install && npm run dev
```

See each folder's README for details:
[backend](backend/README.md) · [recommendsys](recommendsys/README.md) · [frontend](frontend/README.md)
