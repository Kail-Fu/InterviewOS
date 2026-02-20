# InterviewOS Backend

FastAPI backend for assessment invite and reminder flows.

## Endpoints

- `POST /assessments/start`
- `POST /start-assessment` (legacy compatibility alias)
- `POST /api/invite/bulk`
- `POST /api/invite/resend`
- `GET /api/invite/verify?token=...`
- `POST /api/invite/mark-taken`
- `GET /api/assessments`
- `GET /api/assessments/check-title?title=...`
- `GET /api/candidates?assessmentId=...`
- `GET /api/questions`
- `GET /api/questions/{id}`
- `POST /api/new-assessments`
- `GET /health`

## Zero-Account Local Mode (No AWS Required)

```bash
cd /Users/fkl/foretoken/InterviewOS/backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

Default local mode:

- `EMAIL_PROVIDER=console`
- `STORAGE_PROVIDER=local`
- `LOCAL_ASSESSMENT_FILENAME=example_assessment.zip`

So generated download links point to:

- `http://localhost:8000/assets/example_assessment.zip`

Invite state is persisted in local SQLite by default:

- `LOCAL_DB_PATH=data/interviewos.sqlite3`

## SMTP Mode (No AWS, Real Inbox UX)

Run Mailpit:

```bash
docker run --rm -p 1025:1025 -p 8025:8025 axllent/mailpit
```

In `.env`:

```env
EMAIL_PROVIDER=smtp
SMTP_HOST=localhost
SMTP_PORT=1025
```

Open inbox UI:

- `http://localhost:8025`

## AWS Mode (Optional)

Use only when you want SES + S3 providers.

```env
EMAIL_PROVIDER=aws_ses
STORAGE_PROVIDER=s3
AWS_REGION=us-east-1
SES_FROM_EMAIL=verified@your-domain.com
ASSESSMENT_BUCKET=your-bucket
ASSESSMENT_OBJECT_KEY=assessment.zip
```

Provide AWS credentials with permissions for SES and S3.

## Environment Notes

- `CORS_ORIGINS` must be a JSON list.
Examples:
`["*"]`
`["http://localhost:5173"]`

## Troubleshooting

If `fastapi` is missing, your shell is not using the backend venv:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

If `SettingsError` appears for `cors_origins`, fix `.env` value format to JSON list.
