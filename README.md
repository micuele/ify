# Last.fm Vite + Flask Starter

A minimal starter for your app idea:
- **Vite + vanilla TypeScript** frontend
- **Flask** backend
- **Last.fm web auth** flow
- basic result endpoint for later emoji analysis

## Why the backend handles auth

Last.fm web auth redirects the user to Last.fm, returns a `token` to your callback URL, and then requires a call to `auth.getSession` signed with `api_sig` using your shared secret. That secret must stay on the backend.

## Project structure

- `frontend/` — Vite UI
- `backend/` — Flask API/auth server

## Setup

### 1. Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env` with:
- `LASTFM_API_KEY`
- `LASTFM_API_SECRET`
- `FLASK_SECRET_KEY`
- `LASTFM_CALLBACK_URL`
- `FRONTEND_URL`

Run backend:
```bash
python app.py
```

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```

## Last.fm app settings

In the Last.fm API account, set the callback URL to match `LASTFM_CALLBACK_URL`, for example:
```text
http://127.0.0.1:5000/auth/lastfm/callback
```

## MVP routes

### Backend
- `GET /health`
- `GET /auth/lastfm`
- `GET /auth/lastfm/callback`
- `GET /api/me`
- `GET /api/result`
- `POST /logout`

### Frontend
- home page with connect button
- result card page

## What to build next

1. replace demo `build_result()` logic with your emoji algorithm
2. fetch richer listening data from Last.fm
3. add story-card export
