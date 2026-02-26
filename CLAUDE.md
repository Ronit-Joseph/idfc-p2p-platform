# CLAUDE.md — IDFC P2P Platform

## Project
AI-Native Event-Driven Procure-to-Pay platform for IDFC FIRST Bank.
Modular monolith: FastAPI + SQLAlchemy + PostgreSQL (SQLite fallback).

## Quick Commands
```bash
# Database (Docker)
docker compose up -d postgres

# Backend
cd backend && uvicorn main:app --reload --port 8000

# Frontend
cd frontend && npm run dev

# Migrations
cd backend && alembic upgrade head

# Seed data
python -m scripts.seed_db

# Tests
cd backend && pytest

# Reset DB
python -m scripts.reset_db
```

## Architecture
- **Modular monolith**: `backend/modules/` contains 16 domain modules
- **Each module**: `models.py` (SQLAlchemy), `schemas.py` (Pydantic), `routes.py` (FastAPI router), `service.py` (business logic), `events.py` (event definitions)
- **Event bus**: `backend/event_bus.py` — internal async pub/sub, mirrors future Kafka topics
- **Database**: PostgreSQL with schema-per-module isolation. SQLite fallback via `aiosqlite`
- **Frontend**: React 18 + Vite + Tailwind at `frontend/` — unchanged from prototype

## Module Map
| Module | DB Schema | Description |
|--------|-----------|-------------|
| auth | auth | JWT + RBAC (5 roles) |
| suppliers | suppliers | Vendor master from portal |
| budgets | budgets | Budget check, encumbrance |
| purchase_requests | procurement | PR lifecycle |
| purchase_orders | procurement | PO + GRN tracking |
| invoices | invoices | Invoice lifecycle |
| matching | invoices | 2-way/3-way matching |
| gst_cache | gst | Cygnet GST data cache |
| msme_compliance | invoices | 45-day SLA tracking |
| ebs_integration | ebs | Oracle EBS event log |
| ai_agents | ai | AI insights management |
| workflow | workflow | Approval matrices |
| notifications | notifications | Alerts |
| audit | audit | Immutable event log |
| analytics | analytics | Spend aggregation |
| vendor_portal | vendor_portal | Portal event stream |

## Rules
1. **NEVER** put business logic in `routes.py` — use `service.py`
2. **ALL** inter-module communication goes through `event_bus`
3. Keep API response shapes backward-compatible with frontend
4. Store money as **integers (paise)** — ₹1 = 100 paise
5. Use human-readable codes (`SUP001`, `PR2024-001`) as public API IDs
6. UUIDs are internal only — never expose to frontend
7. Every state change publishes an event
8. Audit module logs ALL events

## Key Files
- `backend/main.py` — App factory, router mounting
- `backend/config.py` — All settings via env vars
- `backend/database.py` — Async SQLAlchemy session
- `backend/event_bus.py` — Internal event bus
- `backend/seed.py` — Synthetic data seeder
- `frontend/src/api.js` — Frontend API client

## External Integrations (Mocked)
- **Oracle EBS**: AP/GL/FA only — via `ebs_integration` module
- **Vendor Portal**: Kafka events — via `vendor_portal` module
- **Cygnet GSP**: GST cache — via `gst_cache` module
- **Budget Module**: Sync check — via `budgets` module
