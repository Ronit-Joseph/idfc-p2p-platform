# IDFC P2P Platform -- Deployment Guide

## Local Development

### Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | https://python.org |
| Node.js | 18+ | https://nodejs.org |
| Docker | Latest (optional) | https://docker.com |

### Setup Steps

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install frontend dependencies
cd frontend && npm install && cd ..

# 3. (Optional) Start PostgreSQL via Docker
docker compose up -d postgres

# 4. Start backend (from project root)
uvicorn backend.main:app --reload --port 8001

# 5. Start frontend (separate terminal)
cd frontend && npm run dev
```

Frontend: http://localhost:5173 (proxies `/api` to backend)
Backend: http://localhost:8000
Swagger: http://localhost:8000/docs

### SQLite Mode (No Docker)

Set the `DATABASE_URL` environment variable to skip PostgreSQL:

```bash
# Windows CMD
set DATABASE_URL=sqlite+aiosqlite:///./p2p.db

# Windows PowerShell
$env:DATABASE_URL = "sqlite+aiosqlite:///./p2p.db"

# Linux/macOS
export DATABASE_URL=sqlite+aiosqlite:///./p2p.db
```

---

## Render.com Deployment

### Architecture on Render

The platform deploys as a **single web service** on Render:

1. Backend (FastAPI) serves the API at `/api/*`
2. Frontend (React) is pre-built into `frontend/dist/` and served as static files by FastAPI
3. PostgreSQL is provisioned as a Render managed database

### render.yaml

The project includes a `render.yaml` for Infrastructure-as-Code deployment:

```yaml
services:
  - type: web
    name: idfc-p2p-platform
    runtime: python
    buildCommand: |
      pip install -r requirements.txt
      cd frontend && npm install && npm run build
    startCommand: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: "3.11"
      - key: NODE_VERSION
        value: "18"
```

### Deploy Steps

1. **Create a Render account** at https://render.com

2. **Connect your repository** -- link the GitHub/GitLab repo containing this project.

3. **Create a PostgreSQL database**:
   - Go to Render Dashboard --> New --> PostgreSQL
   - Name: `idfc-p2p-db`
   - Plan: Starter (free) or Standard
   - Copy the **Internal Database URL**

4. **Create a Web Service**:
   - Go to New --> Web Service
   - Connect to your repository
   - Settings:
     - **Build Command**: `pip install -r requirements.txt && cd frontend && npm install && npm run build`
     - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
     - **Environment**: Python 3
   - Or use the `render.yaml` for Blueprint deployment (auto-detects from repo)

5. **Set Environment Variables** on the web service:

   | Variable | Value | Required |
   |----------|-------|----------|
   | `DATABASE_URL` | `postgresql+asyncpg://user:pass@host:5432/dbname` | Yes |
   | `JWT_SECRET` | Random 32+ character string | Yes |
   | `AUTH_ENABLED` | `true` or `false` | No (default: false) |
   | `CORS_ORIGINS` | `https://your-domain.onrender.com` | No (default: `*`) |
   | `PYTHON_VERSION` | `3.11` | No |
   | `NODE_VERSION` | `18` | No |

6. **Deploy** -- Render will:
   - Install Python dependencies
   - Build the React frontend (`npm run build`)
   - Start the FastAPI server
   - The app will be available at `https://your-service.onrender.com`

### Database Provisioning on Render

Render provides managed PostgreSQL databases:

- **Connection string format**: `postgresql://user:password@host:5432/dbname`
- **For async SQLAlchemy**: Convert to `postgresql+asyncpg://user:password@host:5432/dbname`
- The database is accessible only from Render services in the same region (Internal URL) or from anywhere (External URL)
- Free tier databases expire after 90 days. Use Standard plan for persistent data.

After the database is provisioned and the `DATABASE_URL` is set, the application will run migrations automatically on startup (or you can trigger them manually via Render Shell: `cd backend && alembic upgrade head`).

---

## Docker Deployment

### Dockerfile

The project includes a production-ready `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY frontend/dist/ ./frontend/dist/

EXPOSE 10000

WORKDIR /app
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "10000"]
```

### Build and Run

```bash
# 1. Build the frontend first
cd frontend && npm install && npm run build && cd ..

# 2. Build the Docker image
docker build -t idfc-p2p .

# 3. Run the container
docker run -p 10000:10000 \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname \
  -e JWT_SECRET=your-secret-key \
  idfc-p2p
```

The application will be available at http://localhost:10000.

Note: The frontend must be pre-built (`frontend/dist/` must exist) before building the Docker image. The Dockerfile copies the pre-built static files.

---

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string (async format: `postgresql+asyncpg://...`) or SQLite (`sqlite+aiosqlite:///./p2p.db`) | In-memory (prototype) | For DB mode |
| `JWT_SECRET` | Secret key for JWT token signing | `dev-secret` | Production |
| `AUTH_ENABLED` | Enable JWT authentication middleware | `false` | No |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `*` | Production |
| `PORT` | Server port (set automatically by Render) | `8000` (local), `10000` (Docker) | No |

---

## CI/CD Considerations (Future)

The following CI/CD pipeline is recommended but not yet implemented:

### Pipeline Stages

1. **Lint**: `ruff check backend/` + `eslint frontend/src/`
2. **Test**: `pytest backend/tests/` + `npm test` (frontend)
3. **Build**: `npm run build` (frontend) + `docker build`
4. **Deploy**: Push to Render via Git deploy hook or Docker registry

### Branch Strategy

| Branch | Purpose | Deploy Target |
|--------|---------|--------------|
| `main` | Production-ready | Production (Render) |
| `develop` | Integration branch | Staging (Render Preview) |
| `feature/*` | Feature development | PR Preview (Render) |

### Recommended CI Tools

- **GitHub Actions**: For lint, test, and build stages
- **Render Auto-Deploy**: Enabled on `main` branch -- Render rebuilds and deploys on every push
- **Render Preview Environments**: Auto-created for pull requests (requires Render Team plan)

---

## Production Checklist

Before going to production, ensure:

- [ ] `AUTH_ENABLED=true` with proper JWT secret
- [ ] `CORS_ORIGINS` set to specific domain(s), not `*`
- [ ] PostgreSQL database provisioned (not SQLite)
- [ ] Database migrations run (`alembic upgrade head`)
- [ ] Seed data loaded or production data migrated
- [ ] Environment variables set (not hardcoded)
- [ ] HTTPS enabled (automatic on Render)
- [ ] Logging configured for production (structured JSON logs)
- [ ] Health check endpoint (`/api/health`) monitored
- [ ] Database backups configured (Render provides daily backups on Standard plan)
