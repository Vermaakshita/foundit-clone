# Foundit Clone

A production-grade full-stack clone of [Foundit.in](https://www.foundit.in) — India's leading job portal. Built with FastAPI, React 18, and Supabase.

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Running Tests](#running-tests)

---

## Overview

Foundit Clone replicates the core experience of Foundit.in — one of India's largest job portals. Job seekers can search, filter, and apply for jobs, manage their profile and resume, track application statuses, and set personalized job alerts. Employers can post and manage job listings, review applicants, and track hiring pipelines — all within a pixel-perfect UI built to match the original brand.

---

## Tech Stack

### Backend
| Technology | Version | Purpose |
|---|---|---|
| Python | 3.11 | Runtime |
| FastAPI | 0.111 | REST API framework |
| Uvicorn | 0.29 | ASGI server |
| Supabase Python SDK | 2.4.6 | Database + Auth client |
| Pydantic v2 | 2.7.1 | Request / response validation |
| python-jose | 3.3.0 | JWT token signing and verification |
| passlib + bcrypt | 1.7.4 | Password hashing |
| python-dotenv | 1.0.1 | Environment variable loading |

### Frontend
| Technology | Purpose |
|---|---|
| React 18 + TypeScript | UI framework with full type safety |
| Tailwind CSS | Utility-first styling |
| shadcn/ui | Accessible component library |
| TanStack Query v5 | Server state management and data fetching |
| Zustand | Lightweight client state management |
| React Hook Form + Zod | Form handling with schema validation |
| Axios | HTTP client with JWT interceptors |
| Lucide React | Icon library |
| Vite 5 | Build tool and dev server |

### Database & Auth
| Technology | Purpose |
|---|---|
| Supabase (PostgreSQL 17) | Primary relational database with Row Level Security |
| Supabase Auth | User authentication and session management |
| Supabase Storage | Resume and profile photo file storage |

---

## Features

### Job Seeker
- Search jobs with advanced filters — keyword, location, job type, experience range, salary range, remote toggle
- Apply with cover letter and resume upload
- Save jobs and revisit them later
- Track full application lifecycle: `Applied → Shortlisted → Interviewed → Offered / Rejected`
- Build a rich profile: headline, bio, skills, education, work experience
- Manage and upload resumes
- Create job alerts with daily or weekly email frequency
- Seeker dashboard with application stats and activity feed

### Employer
- Post job listings with full detail: role, description, skills, salary, openings, expiry
- Manage job status: `Active`, `Draft`, `Closed`
- Browse and filter applicants per listing
- Update applicant statuses through the hiring pipeline
- Employer dashboard with posting and applicant metrics

### Platform
- JWT authentication with access + refresh token flow
- Role-based access control — seeker vs employer with enforced route guards
- Company profiles with ratings and reviews
- Career advice articles
- Salary insights page
- Fully responsive UI matching Foundit.in brand colors

---

## Project Structure

```
foundit-clone/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app, CORS, router registration
│   │   ├── config.py             # Environment-based settings
│   │   ├── dependencies.py       # JWT auth dependency injection
│   │   ├── models/               # Pydantic schemas
│   │   │   ├── user.py
│   │   │   ├── job.py
│   │   │   ├── application.py
│   │   │   ├── company.py
│   │   │   └── common.py
│   │   ├── routers/              # Route handlers (one file per domain)
│   │   │   ├── auth.py
│   │   │   ├── jobs.py
│   │   │   ├── applications.py
│   │   │   ├── users.py
│   │   │   ├── companies.py
│   │   │   ├── saved_jobs.py
│   │   │   ├── job_alerts.py
│   │   │   ├── skills.py
│   │   │   └── dashboard.py
│   │   └── services/
│   │       └── supabase.py       # Supabase client singleton
│   ├── tests/                    # pytest test suite
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.tsx
│   │   │   ├── JobSearch.tsx
│   │   │   ├── JobDetail.tsx
│   │   │   ├── CompanyProfile.tsx
│   │   │   ├── CareerAdvice.tsx
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   ├── seeker/
│   │   │   │   ├── Dashboard.tsx
│   │   │   │   ├── AppliedJobs.tsx
│   │   │   │   ├── SavedJobs.tsx
│   │   │   │   ├── Profile.tsx
│   │   │   │   ├── Resume.tsx
│   │   │   │   └── JobAlerts.tsx
│   │   │   └── employer/
│   │   │       ├── Dashboard.tsx
│   │   │       ├── PostJob.tsx
│   │   │       ├── MyJobs.tsx
│   │   │       └── Applicants.tsx
│   │   ├── components/
│   │   │   ├── layout/           # Navbar, Footer, DashboardLayout
│   │   │   ├── jobs/             # JobCard, JobFilters, SearchBar, JobCategories
│   │   │   ├── modals/           # ApplyModal, JobAlertModal
│   │   │   └── ui/               # Spinner, EmptyState, Pagination, StatusBadge, SkillTag
│   │   ├── lib/                  # Axios instance, React Query client
│   │   └── store/                # Zustand auth and UI stores
│   ├── .env.example
│   └── vite.config.ts
│
├── .claude/
│   ├── settings.json             # MCP servers, permissions, git hooks
│   ├── commands/                 # 8 custom Claude slash commands
│   └── agents/                   # test-engineer sub-agent
│
├── CLAUDE.md                     # AI agent context and project rules
└── README.md
```

---

## Database Schema

16 tables in Supabase PostgreSQL with Row Level Security enabled on all tables.

| Table | Description |
|---|---|
| `profiles` | User profile — seeker or employer role, bio, photo, resume |
| `companies` | Company listings with industry, size, verification status |
| `jobs` | Job postings with salary range, experience, type, status |
| `skills` | Master skill catalog |
| `job_skills` | Skills required per job posting |
| `user_skills` | Skills on a user profile with proficiency level |
| `education` | User education history |
| `work_experience` | User work history |
| `applications` | Job applications with status lifecycle and AI-generation flag |
| `saved_jobs` | Bookmarked jobs per user |
| `job_alerts` | Saved search alerts with frequency settings |
| `notifications` | In-app notification feed |
| `company_reviews` | Ratings and reviews left on company profiles |
| `career_articles` | Blog-style career advice content |
| `job_views` | Job view tracking |
| `profile_views` | Profile view tracking |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- A [Supabase](https://supabase.com) project (free tier works)

### 1. Clone the repository

```bash
git clone https://github.com/your-username/foundit-clone.git
cd foundit-clone
```

### 2. Backend setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Copy and fill in environment variables
cp .env.example .env
```

Start the backend:

```bash
uvicorn app.main:app --reload
```

- API base: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`

### 3. Frontend setup

```bash
cd frontend

npm install

# Copy and fill in environment variables
cp .env.example .env
```

Start the frontend:

```bash
npm run dev
```

- App: `http://localhost:5173`

---

## Environment Variables

### Backend — `backend/.env`

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
SECRET_KEY=your_random_secret_key_min_32_characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
FRONTEND_URL=http://localhost:5173
```

### Frontend — `frontend/.env`

```env
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-project-ref.supabase.co
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

> All keys are available in your Supabase project under **Settings → API**.

---

## API Reference

Full interactive docs at `http://localhost:8000/docs`.

| Router | Base Path | Key Endpoints |
|---|---|---|
| Auth | `/api/auth` | `POST /register`, `POST /login`, `POST /refresh` |
| Jobs | `/api/jobs` | `GET /` (search + filter), `POST /`, `GET /:id`, `PATCH /:id` |
| Applications | `/api/applications` | `POST /`, `GET /my`, `PATCH /:id/status` |
| Users | `/api/users` | `GET /me`, `PATCH /me`, profile + skills + education |
| Companies | `/api/companies` | `GET /`, `GET /:id`, `POST /`, reviews |
| Saved Jobs | `/api/saved-jobs` | `POST /`, `DELETE /:id`, `GET /my` |
| Job Alerts | `/api/job-alerts` | `POST /`, `GET /my`, `PATCH /:id`, `DELETE /:id` |
| Skills | `/api/skills` | `GET /` (search autocomplete) |
| Dashboard | `/api/dashboard` | Seeker stats, employer stats |

---

## Running Tests

```bash
cd backend

# Run full test suite
pytest

# With coverage report
pytest --cov=app --cov-report=term-missing
```

Tests cover: auth flows, job CRUD, application lifecycle, role enforcement, search filters, saved jobs, and job alerts.

---

## Brand Colors

| Token | Hex |
|---|---|
| Primary Orange | `#f04e23` |
| Dark Navy | `#1a1a2e` |
| Text Dark | `#333333` |
| Text Muted | `#666666` |
| Border | `#e0e0e0` |
| Background | `#f5f5f5` |
| Success | `#28a745` |
| Warning | `#ffc107` |
| Danger | `#dc3545` |

---

## License

MIT
