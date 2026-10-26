# CALDIM IntelliSolve AI

CALDIM IntelliSolve AI is an industrial AI consultation platform for CALDIM products and manufacturing businesses.

> **Status: Phase 2 Complete (PostgreSQL & Persistent Visitor Data)**  
> PostgreSQL 18 is active as the primary application database. Persistent visitor profiles, explicit GDPR-compliant consent management, and consultation sessions are fully implemented and verified against PostgreSQL.

---

## Workspace Structure

```
Caldim_IntelliSolve/
├── backend/                  # Django + Django REST Framework API
│   ├── apps/
│   │   ├── health/           # System health & telemetry endpoint (/api/v1/health/)
│   │   └── visitors/         # Visitor profiles, consent, and sessions (/api/v1/visitors/)
│   ├── core/                 # Django settings, WSGI, ASGI, and URL routing
│   ├── .venv/                # Python virtual environment (ignored in git)
│   ├── .env                  # Local environment file (ignored in git)
│   ├── .env.example          # Backend environment template
│   ├── manage.py             # Django management entrypoint
│   └── requirements.txt      # Python dependencies (Django 6.1, psycopg 3, DRF, etc.)
├── frontend/                 # React 19 + TypeScript (Strict) + Vite
│   ├── src/
│   │   ├── api/              # Centralized typed API client (health & visitor services)
│   │   ├── components/       # Reusable UI & layout primitives (Card, Badge, Button, StatusDot)
│   │   ├── features/         # Feature modules (system-status dashboard)
│   │   ├── hooks/            # Decoupled custom hooks (useSystemHealth)
│   │   ├── styles/           # Design system tokens (tokens.css, index.css)
│   │   └── types/            # Strict TypeScript interfaces (health.ts, visitor.ts)
│   ├── .env.example          # Frontend environment template
│   ├── index.html            # Entry HTML with typography & SEO metadata
│   ├── package.json          # Node dependencies and scripts
│   └── tsconfig.app.json     # TypeScript strict configuration
├── docs/                     # Architectural & Phase Documentation
│   ├── ARCHITECTURE.md       # High-level architecture, security, and API specifications
│   └── IMPLEMENTATION_PHASES.md # Phased roadmap and dependencies
├── infrastructure/           # Infrastructure guides and compose templates
├── .gitignore                # Production-grade git exclusions
├── .env.example              # Monorepo environment configuration template
└── README.md                 # Setup, startup, and troubleshooting guide
```

---

## Database Configuration (PostgreSQL 18)

The backend connects directly to PostgreSQL 18 using the application role `caldim_user` and database `caldim_intellisolve`.

Environment variables configured in `backend/.env`:
```ini
DB_NAME=caldim_intellisolve
DB_USER=caldim_user
DB_PASSWORD=<configured_application_password>
DB_HOST=127.0.0.1
DB_PORT=5432
```
*Note: SQLite fallback is strictly removed. The application enforces PostgreSQL connectivity.*

---

## Quick Start (Windows PowerShell)

Open two PowerShell windows inside `C:\caldim_smartAI\Caldim_IntelliSolve`.

### Window 1: Start Backend API (Django REST Framework)

```powershell
# 1. Navigate to backend directory
cd backend

# 2. Run migrations (if new migrations exist)
.\.venv\Scripts\python.exe manage.py migrate

# 3. Start the Django development server
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

- Health Endpoint: **http://127.0.0.1:8000/api/v1/health/**
- Visitors API: **http://127.0.0.1:8000/api/v1/visitors/**
- Django Admin: **http://127.0.0.1:8000/admin/**

### Window 2: Start Frontend Application (React + Vite)

```powershell
# 1. Navigate to frontend directory
cd frontend

# 2. Start the Vite dev server
npm run dev
```

- Web Application: **http://localhost:5173/**

---

## Administrative Setup (Django Admin)

To create a local administrator for inspecting database records:
```powershell
cd backend
.\.venv\Scripts\python.exe manage.py createsuperuser
```
Follow prompts to set an admin username and password. Then log in at `http://127.0.0.1:8000/admin/`.

---

## Automated Verification & Testing

### 1. Run Backend System Checks
```powershell
backend\.venv\Scripts\python.exe backend\manage.py check
```

### 2. Run End-to-End Persistence Verification
```powershell
backend\.venv\Scripts\python.exe C:\Users\USER\.gemini\antigravity-ide\brain\b673b7c2-b37e-4b75-b485-f17a516e80db\scratch\verify_phase2_endpoints.py
```
*Validates visitor profile creation, token authentication, session establishment, metadata filtering, consent update, and direct raw SQL query from PostgreSQL.*

### 3. Run Frontend Production Build & Strict Type Check
```powershell
npm --prefix frontend run build
```
