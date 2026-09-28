# Screenline — Multi-Agent AI Resume Screening and ATS Analysis System

An academic-grade, production-styled full-stack application that analyzes a candidate's
resume against a job description using **ten specialized AI agents**, a **deterministic
scoring engine**, and a **React dashboard** — instead of a single black-box AI call.

> ⚠️ **Responsible use notice:** This tool produces AI-based *estimates* to support resume
> optimization and candidate self-assessment. It is not a certified ATS product and its
> scores should never be treated as a final hiring decision.

---

## 1. Project Overview

Screenline lets a user:

1. Register/log in.
2. Upload a resume (PDF or DOCX).
3. Paste or write a job description.
4. Run a multi-agent analysis pipeline.
5. Review an ATS score, job match score, and six sub-scores, with matching/missing
   skills, a keyword table, ATS issues, strengths, and prioritized recommendations.
6. Browse, search, sort, and delete past analyses from a history page.
7. View aggregate stats and score trends on a dashboard.

## 2. Features

- Multi-agent AI pipeline (10 agents, see below)
- Deterministic, transparent, configurable scoring engine (weights live in Python, not
  in the LLM)
- ATS compatibility analysis (formatting + content), clearly labeled as an **AI-based
  estimate**, never claimed to match a real company's ATS
- Skill and keyword gap detection with semantic matching
- Fresher-friendly experience scoring (academic projects, internships, certifications,
  hackathons all count — a lack of full-time experience is not automatically penalized
  for entry-level roles)
- Hallucination controls: every agent has a rule-based fallback and is instructed never
  to invent skills, experience, or education not present in the source text
- MySQL persistence with a normalized 8-table schema
- JWT authentication with bcrypt password hashing
- Analysis history with search, sort, and delete
- Professional, responsive React dashboard (desktop/tablet/mobile)

## 3. Architecture

```
                         USER
                          |
                          v
                    REACT FRONTEND  (Vite + Tailwind, port 5173)
                          |  Axios / REST + JWT
                          v
                      FASTAPI BACKEND (port 8000)
                          |
              +-----------+-----------+
              |                       |
              v                       v
        Resume Service           Job Description
     (PDF/DOCX extraction)            CRUD
              |                       |
              +-----------+-----------+
                          |
                          v
                MULTI-AGENT ORCHESTRATOR
                 (app/services/analysis_service.py)
                          |
   1. Resume Parser Agent      ---> structured resume JSON
   2. JD Analyzer Agent        ---> structured JD JSON
   3. ATS Agent                ---> ATS issues / strengths / estimate
   4. Skill Matching Agent     ---> exact/related/missing skills
   5. Keyword Matching Agent   ---> Found / Partially Found / Missing
   6. Experience & Qualification Agent
   7. Resume Quality Agent
                          |
                          v
   8. Scoring Agent (Python, deterministic — NOT the LLM)
                          |
                          v
   9. Recommendation Agent  ---> prioritized, grounded suggestions
                          |
                          v
   10. Final Report Agent   ---> narrative summary (numbers already fixed)
                          |
                          v
                     MySQL (8 tables)
                          |
                          v
                 React Dashboard / Results page
```

### Why multi-agent instead of one prompt?

Each agent has a narrow, auditable responsibility and its own JSON schema, its own
prompt, and — critically — its own deterministic fallback so the pipeline degrades
gracefully instead of failing outright if the AI call errors out. Every agent's raw
output is persisted to the `agent_results` table for debugging/auditability.

### Hybrid scoring model (the most important design decision)

The LLM is **never** allowed to output the final numeric score. Instead:

- Agents 1–7 produce *signals* (parsed structured data, or a sub-score like `ats_score`,
  `skill_score`, etc.)
- **Agent 8 (Scoring Agent)** is pure Python. It combines sub-scores using configurable
  weights from `app/core/config.py`:

  | Component | Weight |
  |---|---|
  | ATS Compatibility | 25% |
  | Job Skill Match | 30% |
  | Keyword Match | 15% |
  | Experience / Relevance | 15% |
  | Education / Certification | 10% |
  | Resume Quality | 5% |

- Status labels (`Strong Match` / `Moderate Match` / `Needs Improvement` / `Low Match`)
  come from configurable thresholds, also in Python, never from the LLM.

## 4. Technology Stack

**Frontend:** React 18, Vite, Tailwind CSS, React Router, Axios, Recharts, lucide-react

**Backend:** Python 3.11, FastAPI, Pydantic, SQLAlchemy, PyMySQL, PyMuPDF, python-docx,
python-jose (JWT), passlib+bcrypt, google-generativeai

**Database:** MySQL 8

## 5. Database Schema

8 normalized tables with foreign keys and indexes:

`users` → `resumes`, `job_descriptions`, `analyses` (1-to-many)
`analyses` → `extracted_skills`, `missing_keywords`, `recommendations`, `agent_results`
(1-to-many, cascade delete)

See `backend/app/models/*.py` for full column definitions.

## 6. API Documentation

Interactive Swagger docs are available at **http://localhost:8000/docs** once the
backend is running (ReDoc at `/redoc`).

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register` | Create an account |
| POST | `/api/auth/login` | Log in, receive a JWT |
| POST | `/api/resumes/upload` | Upload + parse a resume file |
| GET | `/api/resumes` | List your uploaded resumes |
| POST | `/api/job-descriptions` | Save a job description |
| GET | `/api/job-descriptions` | List your saved job descriptions |
| POST | `/api/analyses` | Run the full multi-agent analysis |
| GET | `/api/analyses` | List your analysis history |
| GET | `/api/analyses/{id}` | Get one analysis in full detail |
| DELETE | `/api/analyses/{id}` | Delete an analysis |
| GET | `/api/dashboard` | Aggregate stats for the dashboard |
| GET | `/api/health` | Health check |

## 7. Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- MySQL 8 (or Docker)
- A Google AI Studio API key (optional — the app runs in rule-based fallback mode
  without one; see §10)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then fill in your values
uvicorn app.main:app --reload    # http://localhost:8000
```

The app creates all MySQL tables automatically on startup (`init_db()` in
`app/database/connection.py`). For a real production deployment, replace this with
Alembic migrations.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env              # VITE_API_BASE_URL=http://localhost:8000
npm run dev                       # http://localhost:5173
```

### MySQL setup

```sql
CREATE DATABASE resume_screening_db CHARACTER SET utf8mb4;
CREATE USER 'screenline'@'%' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON resume_screening_db.* TO 'screenline'@'%';
FLUSH PRIVILEGES;
```

Then set `DATABASE_URL=mysql+pymysql://screenline:your_password@localhost:3306/resume_screening_db`
in `backend/.env`.

### Docker Compose (all three services)

```bash
GOOGLE_API_KEY=your_key_here docker compose up --build
```

## 8. Environment Variables

`backend/.env.example`:
```
GOOGLE_API_KEY=
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/resume_screening_db
JWT_SECRET=change_this_to_a_long_random_secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
MAX_UPLOAD_SIZE_MB=5
GOOGLE_MODEL=gemini-1.5-flash
```

`frontend/.env.example`:
```
VITE_API_BASE_URL=http://localhost:8000
```

**Never** commit a real `.env` file. The API key, DB password, and JWT secret are read
only from environment variables and are never sent to or embedded in the frontend
bundle.

## 9. Google AI Studio API Setup

1. Go to https://aistudio.google.com/app/apikey and create a free API key.
2. Put it in `backend/.env` as `GOOGLE_API_KEY=...`.
3. `GOOGLE_MODEL` defaults to `gemini-1.5-flash` (fast/cheap; good for structured JSON
   output). You can swap in another Gemini model name if you have access.

## 10. Fallback Mode (running without an API key)

Every one of the 7 AI-backed agents has a rule-based fallback in the same file (see the
`_fallback_*` function in each `app/agents/*.py`), using section-header parsing and a
curated skill vocabulary (`app/utils/text_extraction_helpers.py`). This means:

- The app is fully runnable and demoable with **zero cost and no API key**.
- Fallback results are less semantically rich than the LLM path (no synonym matching,
  e.g. "ML" ↔ "Machine Learning"), but are never empty/fake — they're grounded in
  actual resume/JD text.
- Every agent result stores `_fallback_mode: true/false` in `agent_results` so you can
  see which path was used for a given analysis, which is a good interview talking point.

## 11. Testing

Backend tests (pytest, uses in-memory SQLite so no live MySQL is required):

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

Included tests: auth register/login + password-mismatch validation, deterministic
scoring math, and file-extension validation. Add more under `backend/tests/` following
the same `client`/`db_session` fixtures in `tests/conftest.py`.

Sample data for manual testing lives in `sample_data/`: three job descriptions
(Software Developer, Data Analyst, ML Engineer) and one fresher resume.

## 12. Known Limitations

- No Alembic migration system — schema changes currently require dropping/recreating
  tables (fine for a student project, not for production).
- The fallback (no-API-key) mode does not do semantic/synonym skill matching — only
  literal keyword-spotting against a fixed vocabulary.
- No email verification or password-reset flow.
- No rate limiting on the AI endpoints — for a public deployment, add per-user request
  throttling in front of `/api/analyses`.
- Resume parsing accuracy depends on the source PDF being text-based; scanned/image-only
  PDFs will correctly fail with the "Unable to extract text..." error rather than silently
  returning empty data.

## 13. Future Enhancements

- Alembic migrations + seed script
- Support for multiple resume versions per job application, with diffing between analyses
- Batch analysis mode (one resume vs. many JDs, or vice versa)
- Fine-grained per-agent retry/backoff dashboards for observability
- Optional PII redaction pass before sending resume text to the LLM

---

## 14. How to Explain This Project in an Interview

**Problem:** Students and early-career candidates often don't know why their resume
gets filtered out before a human ever reads it, and generic "resume checker" tools give
vague, unhelpful feedback.

**Solution:** A system that scores a resume against a *specific* job description across
six transparent, separately-weighted dimensions (ATS formatting, skill match, keyword
match, experience/relevance, education, writing quality), instead of one opaque number.

**Architecture:** A React SPA talks to a FastAPI backend over a JWT-authenticated REST
API. The backend's core is a ten-stage agent pipeline: each agent has one job, one
prompt, one JSON schema, and one deterministic fallback. Results are persisted at every
stage (`agent_results` table) for auditability.

**AI agents:** Explain the split between *semantic* work (skill/keyword matching,
grammar, JD understanding — where an LLM adds real value) and *deterministic* work
(the actual score, percentages, database writes — where you want reproducibility, not
LLM creativity). This hybrid design is the single most defensible architectural choice
in the project and is worth leading with.

**Scoring:** Be ready to state the weights from memory (25/30/15/15/10/5) and explain
*why* skill match is weighted highest (it's the strongest signal of job fit) and resume
quality lowest (it's real but secondary to actual qualification).

**Database:** Walk through the 8-table schema and explain the cascade-delete
relationships (deleting a user cleans up everything they created; deleting an analysis
cleans up its skills/keywords/recommendations/agent results).

**Challenges you hit and fixed while building it** (genuinely encountered, worth
mentioning): a bcrypt/passlib version incompatibility that broke password hashing
silently; SQLite in-memory test fixtures needing `StaticPool` to share a connection
across requests in tests; and designing rule-based fallbacks that are good enough to
demo the product's value even without paying for LLM calls.

**Future improvements:** Mention Alembic migrations, batch analysis, and PII redaction
as thoughtful next steps — shows you know where the corners were cut and why.

---

## 15. Test Credentials

No seeded accounts are created automatically (would mean shipping a default password).
Register a new account at `/register` — the first account you create is fully
functional immediately; there's no admin approval step.
