# InterviewOS

**Open infrastructure for real-work technical assessments.**

InterviewOS helps companies evaluate candidates through job-relevant tasks instead of algorithm puzzles. Candidates complete realistic assignments using their normal tools, while InterviewOS records their workflow and generates structured evaluation reports.

The goal is simple: measure how someone actually works before you hire them.

---

## Why InterviewOS Exists

Work has changed with AI, but hiring has not.

Many companies still rely on short coding challenges that reward preparation rather than job readiness. These interviews rarely show how a candidate debugs unfamiliar code, uses documentation, works with AI tools, or communicates decisions.

InterviewOS exists to help move hiring toward employer-hosted, real-work simulations and away from leetcode-style filtering.

---

## What InterviewOS Does

### For Companies

**Create assessments**  
Define the task, follow-up questions, and report requirements.

**Invite candidates**  
Send secure email links. No account setup required.

**Review structured reports**  
Each report includes scores, responses, and a full screen recording so reviewers can see exactly how the candidate approached the work.

---

### For Candidates

**Accept via link**  
Start the assessment directly from the invitation.

**Work normally**  
Use your preferred tools and complete the task end-to-end while your screen is recorded.

**Explain your thinking**  
Answer follow-up questions to provide context for your decisions.

**View your report (optional)**  
Companies can enable report sharing for transparency.

---

## Designed for Reliable Evaluation

InterviewOS includes safeguards to help companies trust the results:

- Runs entirely in the browser. No software to install  
- Email-based authentication  
- Protection against multiple attempts  
- Optional camera verification  
- Full workflow recording, not just final code  

The focus is not only what candidates produce, but how they get there.

---

## When to Use InterviewOS

InterviewOS is useful anywhere a short puzzle falls short:

- Backend or frontend engineering roles  
- Machine learning positions  
- Debugging-heavy jobs  
- Tool-driven workflows  
- AI-assisted development environments  

If the role involves real work, it can be simulated.

---

## What Works Today

- End-to-end invite flow with frontend + backend
- `POST /assessments/start` plus legacy `POST /start-assessment`
- Local out-of-box mode with no AWS account required
- Bundled sample assessment archive for immediate testing
- Local SMTP inbox via Mailpit in Docker Compose setup

---

## Run End-to-End (One Command)

Prerequisite: Docker Desktop running.

```bash
make dev
```

This starts:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Mailpit inbox: `http://localhost:8025`

Bundled sample assessment file:

- `/Users/fkl/foretoken/InterviewOS/backend/assets/example_assessment.zip`

---

## Roadmap

Planned next steps:

- Assessment execution state (attempt start/end/expiration)
- Submission upload pipeline
- Automated evaluation and rubric scoring
- Screen/workflow recording ingestion and analysis
- Structured candidate report generation
- Reviewer dashboard and collaboration workflow
- ATS and webhook integrations

---

## Contributing

- `/Users/fkl/foretoken/InterviewOS/CONTRIBUTING.md`

## Security

- `/Users/fkl/foretoken/InterviewOS/SECURITY.md`

---

## Hosted Option

InterviewOS is the open infrastructure.

If you prefer a fully managed assessment platform with ready-to-use simulations, automated scoring, and enterprise features, you can use the hosted version at:

https://foretokenai.com

---

## License

MIT
