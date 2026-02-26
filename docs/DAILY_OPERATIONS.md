# IDFC P2P Platform -- Daily Operations

## Prerequisites

| Requirement | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Backend (FastAPI) |
| Node.js | 18+ | Frontend (React + Vite) |
| Docker | Optional | PostgreSQL container |
| Git | Latest | Version control |

## Local Development Setup

### Option A: With Docker (PostgreSQL)

```bash
# 1. Start PostgreSQL
docker compose up -d postgres

# 2. Run database migrations
cd backend
alembic upgrade head

# 3. Seed synthetic data
python -m scripts.seed_db

# 4. Start backend (Terminal 1)
cd backend
uvicorn main:app --reload --port 8000

# 5. Start frontend (Terminal 2)
cd frontend
npm install       # first time only
npm run dev
```

Backend runs at: http://localhost:8000
Frontend runs at: http://localhost:5173
Swagger docs at: http://localhost:8000/docs

### Option B: SQLite Mode (No Docker)

Set the environment variable to use SQLite instead of PostgreSQL:

```bash
# Windows CMD
set DATABASE_URL=sqlite+aiosqlite:///./p2p.db

# Windows PowerShell
$env:DATABASE_URL = "sqlite+aiosqlite:///./p2p.db"

# Linux/macOS
export DATABASE_URL=sqlite+aiosqlite:///./p2p.db
```

Then follow steps 2-5 from Option A. SQLite creates a single `p2p.db` file in the working directory.

### Option C: Quick Start (Prototype Mode)

The prototype runs entirely from `backend/main.py` with in-memory synthetic data -- no database setup needed:

```bash
# Terminal 1 -- Backend
cd backend
python -m uvicorn main:app --reload --port 8000

# Terminal 2 -- Frontend
cd frontend
npm install       # first time only
npm run dev
```

Or use the batch files:
- Double-click `start_backend.bat`
- Double-click `start_frontend.bat`

## Running Tests

```bash
cd backend
pytest

# With verbose output
pytest -v

# Specific test file
pytest tests/test_invoices.py

# With coverage
pytest --cov=.
```

## Database Operations

### Run Migrations

```bash
cd backend
alembic upgrade head
```

### Create a New Migration

```bash
cd backend
alembic revision --autogenerate -m "description of change"
```

### Seed Database

```bash
python -m scripts.seed_db
```

This loads 15 suppliers, 8 PRs, 3 POs, 7 invoices, 15 GST cache records, 8 EBS events, 7 AI insights, and 6 vendor portal events.

### Reset Database

```bash
python -m scripts.reset_db
```

This drops all tables and re-runs migrations + seed.

## Adding a New Module

1. **Create the module directory**:
   ```bash
   mkdir backend/modules/my_module
   ```

2. **Create the standard files**:
   ```
   backend/modules/my_module/
       __init__.py
       models.py      # SQLAlchemy models
       schemas.py     # Pydantic schemas
       routes.py      # FastAPI router
       service.py     # Business logic
       events.py      # Event definitions
   ```

3. **Define your models** in `models.py` using SQLAlchemy 2.0 declarative style.

4. **Create the router** in `routes.py`:
   ```python
   from fastapi import APIRouter
   router = APIRouter(prefix="/api/my-module", tags=["my-module"])
   ```

5. **Register the router** in `backend/main.py`:
   ```python
   from modules.my_module.routes import router as my_module_router
   app.include_router(my_module_router)
   ```

6. **Publish events** in `service.py` via the event bus:
   ```python
   from backend.event_bus import event_bus
   await event_bus.publish("my_module.created", payload)
   ```

7. **Generate migration**:
   ```bash
   cd backend
   alembic revision --autogenerate -m "add my_module tables"
   alembic upgrade head
   ```

## Key Rules

1. **Never put business logic in `routes.py`** -- always delegate to `service.py`.
2. **All inter-module communication goes through the event bus** -- no direct imports between modules.
3. **Store money as integers (paise)** -- 1 INR = 100 paise.
4. **Use human-readable codes** (`SUP001`, `PR2024-001`) as public API identifiers.
5. **UUIDs are internal only** -- never expose to the frontend.
6. **Keep API response shapes backward-compatible** with the existing frontend.

## Troubleshooting

### Backend won't start

- **Port already in use**: Kill the process on port 8000, or start on a different port with `--port 8001`.
- **Module import error**: Ensure you are running from the correct directory (`cd backend`).
- **Missing dependencies**: Run `pip install -r requirements.txt` from the project root.

### Frontend won't start

- **Port 5173 in use**: Vite will auto-increment to 5174. Check terminal output.
- **Missing node_modules**: Run `npm install` in the `frontend/` directory.
- **Proxy errors (502)**: Ensure the backend is running on port 8000 before starting the frontend.

### Database issues

- **Connection refused (PostgreSQL)**: Ensure Docker is running: `docker compose up -d postgres`.
- **Migration errors**: Try resetting: `python -m scripts.reset_db`.
- **SQLite locked**: Only one process can write to SQLite at a time. Use PostgreSQL for concurrent access.

### API returns empty data

- If using the database-backed mode, run `python -m scripts.seed_db` to populate data.
- If using prototype mode (`backend/main.py` with in-memory data), data is always available on startup.

### Frontend shows blank page

- Check browser console (F12) for errors.
- Ensure the `/api` proxy in `vite.config.js` points to the correct backend port.
- Verify the backend is returning JSON at http://localhost:8000/api/health.

### CORS errors

- In development, the backend allows all origins (`allow_origins=["*"]`).
- In production, set `CORS_ORIGINS` environment variable to the frontend domain.

## Useful URLs (Local Dev)

| URL | Description |
|-----|-------------|
| http://localhost:5173 | Frontend (Vite dev server) |
| http://localhost:8000 | Backend (FastAPI) |
| http://localhost:8000/docs | Swagger UI (interactive API docs) |
| http://localhost:8000/redoc | ReDoc (alternative API docs) |
| http://localhost:8000/api/health | Health check endpoint |
| http://localhost:8000/api/dashboard | Dashboard data |
