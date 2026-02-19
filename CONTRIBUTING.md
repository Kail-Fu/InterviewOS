# Contributing to InterviewOS

## Development Setup

### One-command stack (recommended)

```bash
make dev
```

### Backend-only

```bash
cd /Users/fkl/foretoken/InterviewOS/backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend-only

```bash
cd /Users/fkl/foretoken/InterviewOS/frontend
npm install
npm run dev
```

## Pull Request Guidelines

- Keep changes focused and small.
- Update docs for any user-visible behavior changes.
- Keep local mode (`EMAIL_PROVIDER=console` and `STORAGE_PROVIDER=local`) working.
- Preserve backward compatibility for `POST /start-assessment` unless explicitly removing it in a breaking release.

## Pre-PR Checks

- Backend starts successfully.
- Frontend can submit invite to backend.
- Invite email appears in Mailpit (or console logs).
- Reminder email is sent.
