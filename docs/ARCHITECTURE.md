# IDFC P2P Platform -- System Architecture

## Overview

The IDFC P2P (Procure-to-Pay) Platform is an AI-native, event-driven system built for IDFC FIRST Bank. It replaces Oracle EBS PR/PO/Invoice UI with a purpose-built platform while retaining Oracle EBS solely as the financial ledger backend (AP, AR, GL, Fixed Assets).

## Architecture Pattern: Modular Monolith

The backend follows a **modular monolith** pattern -- a single deployable FastAPI application partitioned into 16 domain modules under `backend/modules/`. This provides clear domain boundaries that can be extracted into independent microservices in the future when Kafka and service mesh infrastructure are ready.

### Current State (v0.5.0 -- Sprint 4 Complete)

All 19 modules are fully DB-backed with SQLAlchemy ORM models, Pydantic schemas, service layers, and FastAPI routers. The system serves 75+ API endpoints, 18 frontend pages, and an internal event bus that auto-persists all events to an immutable audit trail. SQLite is the default database for zero-Docker development; PostgreSQL is supported via `DATABASE_URL`.

Each module under `backend/modules/` contains:

| File | Purpose |
|------|---------|
| `models.py` | SQLAlchemy ORM models |
| `schemas.py` | Pydantic request/response schemas |
| `routes.py` | FastAPI router (thin -- delegates to service) |
| `service.py` | Business logic (all domain rules live here) |
| `events.py` | Event definitions published/consumed by the module |

### Module Map

| Module | DB Schema | Description |
|--------|-----------|-------------|
| `auth` | auth | JWT authentication + RBAC (5 roles) |
| `suppliers` | suppliers | Vendor master synced from portal |
| `budgets` | budgets | Budget check, encumbrance tracking |
| `purchase_requests` | procurement | PR lifecycle (create, approve, reject, PO creation) |
| `purchase_orders` | procurement | PO + GRN tracking |
| `invoices` | invoices | Invoice lifecycle (capture through EBS posting) |
| `matching` | invoices | 2-way and 3-way matching engine |
| `gst_cache` | gst | Cygnet GSP GST data cache |
| `msme_compliance` | invoices | MSME Section 43B(h) 45-day SLA tracking |
| `ebs_integration` | ebs | Oracle EBS event log and posting |
| `ai_agents` | ai | AI insights management (5 agents) |
| `workflow` | workflow | Multi-level approval engine with configurable matrices |
| `notifications` | notifications | Severity-based alerts (CRITICAL/HIGH/MEDIUM/LOW) |
| `audit` | audit | Immutable event log -- auto-captured via event bus (7-year RBI retention) |
| `analytics` | analytics | Spend aggregation and KPIs |
| `vendor_portal` | vendor_portal | Vendor portal event stream |
| `payments` | payments | Bank payment runs (NEFT/RTGS/IMPS), TDS deduction, UTR tracking |
| `tds` | tds | TDS management -- Sec 194C/J/H/I/Q/A, auto-calc with 4% H&E cess |
| `documents` | documents | Document metadata with versioning, checksums, soft delete |

## Internal Async Event Bus

File: `backend/event_bus.py`

The internal event bus provides async pub/sub communication between modules. It mirrors the Kafka topic structure planned for production.

```
Service (publisher) --> EventBus --> Subscribers
                                    |-- Audit (logs all events)
                                    |-- Notifications (alerts)
                                    |-- Analytics (spend aggregation)
```

### Design Rules

1. **ALL inter-module communication goes through the event bus** -- modules never import each other's services directly.
2. **Every state change publishes an event** -- creating a PR, approving an invoice, posting to EBS, etc.
3. The **Audit module subscribes to all events** and writes an immutable log.

### Event Topic Mapping (Future Kafka)

| Internal Event | Future Kafka Topic |
|----------------|-------------------|
| `pr.created` | `p2p.procurement.pr-created` |
| `pr.approved` | `p2p.procurement.pr-approved` |
| `po.created` | `p2p.procurement.po-created` |
| `invoice.captured` | `p2p.invoice.captured` |
| `invoice.matched` | `p2p.invoice.matched` |
| `invoice.approved` | `p2p.invoice.approved` |
| `ebs.posted` | `p2p.ebs.posted` |
| `vendor.onboarded` | `p2p.vendor.onboarded` |
| `gst.synced` | `p2p.gst.synced` |

## Database Architecture

### Primary: PostgreSQL 16

- **Schema-per-module isolation** -- each module owns its own database schema (e.g., `auth`, `suppliers`, `procurement`, `invoices`, `gst`, `ebs`, `ai`, `workflow`, `notifications`, `audit`, `analytics`, `vendor_portal`)
- **Async SQLAlchemy 2.0** with `asyncpg` driver
- Managed via **Alembic** migrations (`backend/migrations/`)
- Connection pooling via SQLAlchemy async engine

### Fallback: SQLite

For local development without Docker:
```
DATABASE_URL=sqlite+aiosqlite:///./p2p.db
```

SQLite mode collapses all schemas into a single database file but preserves the same table structure.

### Key Conventions

- All monetary amounts stored as **integers in paise** (INR smallest unit: 1 rupee = 100 paise)
- Human-readable codes (`SUP001`, `PR2024-001`, `PO2024-001`, `INV001`) used as **business identifiers** in API responses
- UUIDs used as **internal primary keys** -- never exposed to the frontend

## Frontend Architecture

| Component | Technology |
|-----------|-----------|
| Framework | React 18 |
| Build tool | Vite 4.x |
| Styling | Tailwind CSS 3.x |
| Charts | Recharts 2.x |
| HTTP client | Axios |
| Routing | React Router DOM 6.x |
| Icons | Lucide React |

### Pages (18)

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/dashboard` | KPIs, spend trend, MSME alerts, EBS failures, activity feed |
| Purchase Requests | `/purchase-requests` | Full PR lifecycle with live budget check |
| Purchase Orders | `/purchase-orders` | PO detail with GRN match and EBS status |
| Invoices | `/invoices` | Invoice list with GST, 3-way match, AI coding, MSME SLA |
| Invoice Detail | `/invoices/:id` | Single invoice deep dive -- all subsystems visible |
| Matching Engine | `/matching` | 2-way/3-way match results, exception queue, resolve actions |
| Payments | `/payments` | Payment runs (NEFT/RTGS/IMPS), individual payments, UTR tracking |
| TDS Management | `/tds` | TDS deductions by section, rate card, auto-calc with cess |
| GST Cache | `/gst-cache` | Cygnet sync strategy, GSTIN registry, sync button |
| MSME Compliance | `/msme` | SLA countdown, breach alerts, Sec 43B(h) penalty |
| Oracle EBS Sync | `/ebs` | Integration event log, scope, retry failed events |
| Workflow | `/workflow` | Multi-level approval instances, approve/reject, matrix rules |
| Documents | `/documents` | Document list by entity type, version badges, file sizes |
| Notifications | `/notifications` | Severity-based alerts, mark read, unread count |
| Audit Trail | `/audit` | Immutable event log, module filter chips, entity search |
| AI Agents | `/ai-agents` | 5 agents, confidence scores, reasoning, apply actions |
| Spend Analytics | `/analytics` | Spend charts, budget vs actual, top vendors |
| Suppliers | `/suppliers` | Supplier registry, vendor portal events, risk scores |

### Data Flow

```
Frontend (React)
    |
    | HTTP (Axios)
    |
Vite Dev Proxy (:5173 --> :8000)
    |
FastAPI Backend (:8000)
    |
    |-- /api/* endpoints
    |
SQLAlchemy Async ORM
    |
PostgreSQL / SQLite
```

In production, the React app is built (`npm run build`) and served as static files by FastAPI from `frontend/dist/`.

## External Integrations

All integrations are **mocked** in the prototype. The module structure and API contracts are designed for real integration.

### 1. Oracle EBS (via Oracle Integration Cloud)

- **Scope retained**: AP (Accounts Payable), GL (General Ledger), FA (Fixed Assets)
- **Scope retired from EBS**: PR, PO, Invoice UI -- replaced by this platform
- **Integration pattern**: Event-driven -- P2P publishes events, OIC translates to EBS ISG REST calls
- **Module**: `ebs_integration`
- **Event types**: PO_COMMITMENT, INVOICE_POST, GL_JOURNAL, FA_ADDITION

### 2. Vendor Portal (via Kafka Events)

- **Separate independently-built system** -- not part of this codebase
- **Integration pattern**: Kafka event stream (consume vendor lifecycle events)
- **Module**: `vendor_portal`
- **Event types**: `vendor.onboarded`, `vendor.bank_verified`, `vendor.gstin_updated`, `vendor.document_expired`

### 3. Cygnet GSP (GST Service Provider)

- **Strategy**: Batch sync GST data into local cache -- no per-invoice API calls
- **Live calls only**: IRN generation, IRN cancellation, e-way bill generation
- **Module**: `gst_cache`
- **Cached data**: GSTIN status, GSTR-1 filing status, GSTR-2B ITC eligibility, registration type

### 4. Budget Module (Bank Internal)

- **Pattern**: REST sync call for budget availability check during PR creation
- **Module**: `budgets`
- **Operations**: Check available budget, commit/release encumbrance

## AI Agents (5)

| Agent | Model | Purpose |
|-------|-------|---------|
| InvoiceCodingAgent | Fine-tuned BERT | Auto-assign GL account and cost center |
| FraudDetectionAgent | Isolation Forest | Detect duplicate/anomalous invoices |
| SLAPredictionAgent | Gradient Boost | Predict MSME payment SLA breaches |
| CashOptimizationAgent | Reinforcement Learning | Suggest optimal payment timing |
| RiskAgent | XGBoost | Score supplier risk based on filing, documents |

All agents are managed through the `ai_agents` module with insight tracking (confidence scores, reasoning traces, applied/pending status).

## Security and Compliance

- **Authentication**: OAuth 2.0 / OIDC (JWT tokens) -- integrates with bank IAM
- **Authorization**: RBAC with 5 roles
- **Audit**: Immutable event log with 7-year retention (RBI requirement)
- **GST compliance**: GSTIN validation, GSTR-2B reconciliation, IRN via Cygnet
- **MSME compliance**: Section 43B(h) 45-day payment SLA with automated breach detection and penalty calculation
- **TDS**: Deduction by vendor category, Form 16A tracking
