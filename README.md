# InterviewOS

<p align="center">
  <img src="assets/gifs/01-create-assessment.gif" width="800" alt="Create an assessment">
</p>

<p align="center">
  <strong>Replace coding puzzles with real-work simulations.</strong><br/>
  Open infrastructure for production-grade technical assessments.
</p>

<p align="center">
  <a href="./LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <a href="#run-locally-in-one-command"><img alt="Docker" src="https://img.shields.io/badge/docker-required-blue.svg"></a>
  <img alt="Version" src="https://img.shields.io/badge/version-1.0.0-informational.svg">
</p>

---

## What is InterviewOS?

InterviewOS helps teams evaluate candidates through job-relevant tasks instead of algorithm puzzles.

Candidates complete realistic assignments using their normal tools. InterviewOS records the full workflow and generates structured evaluation reports so reviewers can see:

- what the candidate shipped
- how they approached the work
- how they debugged, used tools, and made tradeoffs
- how they explained decisions along the way

Not just output. The process.

---

## How it works

### 1) Create an assessment

<p align="center">
  <img src="assets/gifs/01-create-assessment.gif" width="800" alt="Set up an assessment">
</p>

Define the task, add follow-up questions, and configure reporting requirements.

### 2) Invite a candidate

<p align="center">
  <img src="assets/gifs/02-invite-and-accept.gif" width="800" alt="Invite and accept">
</p>

Send a secure link. No account setup required.

### 3) Candidate completes the work end-to-end

<p align="center">
  <img src="assets/gifs/03-workflow-recording.gif" width="800" alt="Candidate completes assessment with recording">
</p>

Candidates work normally using their preferred tools. InterviewOS captures the workflow and responses.

### 4) Review a structured report

<p align="center">
  <img src="assets/gifs/04-generated-report.gif" width="800" alt="Generated report">
</p>

Reviewers get a high-signal summary plus the underlying evidence needed for calibration.

---

## Why InterviewOS exists

Hiring is still optimized for puzzle performance. Modern engineering is not.

Real work involves:

- debugging unfamiliar code
- reading and applying documentation
- using AI tools responsibly
- working through ambiguity
- communicating tradeoffs and decisions

Short algorithm challenges rarely measure these skills. InterviewOS is opinionated: real work beats rehearsed tricks.

---

## InterviewOS vs traditional coding interviews

| Traditional puzzle interviews | InterviewOS |
|---|---|
| tests memorization and prep | tests job-relevant execution |
| output-focused | workflow and decision-focused |
| easy to game | harder to fake |
| no realistic context | realistic tasks and constraints |
| weak reviewer calibration | evidence-rich review (recording + report) |

---

## Run locally in one command

Prerequisite: Docker Desktop running.

```bash
make dev
````

This starts:

* Frontend: [http://localhost:5173](http://localhost:5173)
* Backend API: [http://localhost:8000](http://localhost:8000)
* Local email inbox (Mailpit): [http://localhost:8025](http://localhost:8025)

A bundled sample assessment is included so you can test the full flow immediately.

---

## What works today

* end-to-end invite flow with frontend + backend
* `POST /assessments/start` plus legacy `POST /start-assessment`
* invite lifecycle APIs: bulk send, resend, verify token, and mark-taken
* local out-of-box mode (no AWS account required)
* bundled sample assessment archive for immediate testing
* local SMTP inbox via Mailpit in Docker Compose
* admin dashboard foundation at `/dashboard` backed by:
  * `GET /api/assessments`
  * `GET /api/candidates?assessmentId=<id>`
* assessment creation flow foundation:
  * `/new-assessment` (title + context)
  * `/selection-questions` (question pick + create)
  * `GET /api/questions`, `GET /api/assessments/check-title`, `POST /api/new-assessments`
* assessment result + invite-management foundation:
  * `/assessment_result/:id`
  * `GET /api/assessments/{id}`
  * `POST /api/invite/bulk` and `POST /api/invite/resend` now support `assessmentId` / `candidateId`
  * resend UX polish: success toast + status label rendered as `resent at <timestamp>`
* candidate flow baseline at `/take-assessment?token=...` using copied `Assessment.js` recording pipeline with compatibility endpoints:
  * `GET /api/public/assessment/{id}`
  * `GET /api/reflection/sections`
  * `POST /get-presigned-upload-url`, `PUT /local-upload/{key}`, `POST /notify-recording-upload`
  * `POST /api/recording/start-multipart-upload`, `POST /api/recording/upload-part`, `POST /api/recording/complete-multipart-upload`
  * `POST /upload-zip`, `POST /download-assessment`
* report experience baseline:
  * report route at `/report/:id` backed by persisted candidate report payloads from local artifacts
  * report API compatibility endpoint: `GET /report/{id}`
  * assessment-result action now includes `View Report`
  * `POST /upload-zip` now triggers assessment-linked background scoring dispatch and persists report records in local SQLite
  * local screen-time analyzer hook is enabled for uploaded workflow recordings (duration-based baseline in OSS mode)
  * candidate completion now lands on a loading screen that polls report readiness and auto-redirects to `/report/:id`
  * assessment4 dual-artifact upload path is supported via `POST /upload-assessment4` (submission zip + notebook)

---

## Architecture (high level)

InterviewOS is split into:

* `frontend/`: candidate and admin UI
* `backend/`: API, invite lifecycle, local SQLite state, assessment packaging, and report scoring pipeline
* `docker-compose.yml`: local end-to-end dev environment (including Mailpit)

For development details, see [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Roadmap

Planned next steps:

* recording reliability hardening for multipart and resume/error handling
* deepen report parity (`newreport`) with richer diff/code-review panels and media playback
* tighten candidate-to-report linkage so completion always resolves to the correct report id
* expand evaluator parity from baseline checks to old-repo full autograder/test-case flows by assessment type
* automated evaluation and rubric scoring
* ATS and webhook integrations

---

## Status

InterviewOS `v1.0.0` is production-ready for the open-source local workflow. Core migration includes invite, dashboard, assessment creation/result, candidate assessment flow, recording upload, and generated report viewing with readiness polling.

If you try it and hit sharp edges, please open an issue. Feature requests and PRs are welcome.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Security

See [SECURITY.md](SECURITY.md). Please report sensitive issues responsibly.

---

## Hosted version

InterviewOS is the open infrastructure.

If you prefer a fully managed platform with ready-to-use simulations, automated scoring, and enterprise features:

[https://foretokenai.com](https://foretokenai.com)

---

## License

MIT. See [LICENSE](LICENSE).
