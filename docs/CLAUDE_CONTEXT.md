# IDFC P2P Platform -- AI Assistant Context

This file provides full project context for AI assistant sessions. Use it to rapidly restore context after compaction or at the start of a new session.

## Project Identity

- **Name**: IDFC P2P Platform (Procure-to-Pay)
- **Client**: IDFC FIRST Bank
- **Purpose**: Replace Oracle EBS PR/PO/Invoice UI with a purpose-built AI-native P2P platform
- **Working directory**: `c:\Users\ronit\Documents\code\idfc_projs\p2p`
- **Blueprint**: `AI_Native_Event_Driven_P2P_Platform_Blueprint.docx` (in project root)

## Critical Design Constraints

1. **Oracle EBS** is retained ONLY as financial ledger backend -- AP, AR, GL, Fixed Assets. All PR/PO/Invoice UI is replaced by this platform.
2. **Vendor Management Portal** is a separate, independently-built system. It integrates via Kafka events + REST. Do NOT build vendor onboarding flows in this platform.
3. **Cygnet GSP** is the bank's GST Service Provider. GST data must be cached locally via batch sync -- no per-invoice API calls. Only live calls allowed: IRN generation, IRN cancellation, e-way bill generation.
4. The platform must work **standalone** and also plug into the bank's existing **budget provisioning module**.

## Architecture

- **Pattern**: Modular monolith (FastAPI) with 19 domain modules under `backend/modules/`
- **Current state**: v0.5.0 (Sprint 4 complete) -- all modules fully DB-backed with SQLAlchemy ORM, 75+ endpoints, 18 frontend pages
- **Each module**: `models.py`, `schemas.py`, `routes.py`, `service.py`, `events.py`
- **Event bus**: `backend/event_bus.py` -- internal async pub/sub. Audit module auto-captures all events.
- **Database**: SQLite default for zero-Docker dev. PostgreSQL 16 supported via `DATABASE_URL` env var.
- **Frontend**: React 18 + Vite + Tailwind CSS (18 pages across 4 sidebar groups)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.11+) |
| ORM | SQLAlchemy 2.0 async |
| Database | PostgreSQL 16 / SQLite (fallback) |
| Frontend | React 18 + Vite 4 + Tailwind CSS 3 |
| Charts | Recharts 2 |
| HTTP client | Axios |
| Routing | React Router DOM 6 |
| Icons | Lucide React |
| Deployment | Render.com / Docker |

## Module Map (19 Modules)

| Module | DB Schema | Key Entities |
|--------|-----------|-------------|
| auth | auth | users, roles, sessions |
| suppliers | suppliers | supplier master records |
| budgets | budgets | budget allocations, encumbrances |
| purchase_requests | procurement | PRs, PR line items |
| purchase_orders | procurement | POs, PO line items, GRNs |
| invoices | invoices | invoices, invoice line items |
| matching | invoices | match results (2-way, 3-way), matching exceptions |
| gst_cache | gst | GSTIN records, sync status |
| msme_compliance | invoices | SLA tracking, breach records |
| ebs_integration | ebs | EBS events (AP, GL, FA postings) |
| ai_agents | ai | AI insights, agent config |
| workflow | workflow | approval matrices, approval instances, approval steps |
| notifications | notifications | severity-based alerts (CRITICAL/HIGH/MEDIUM/LOW) |
| audit | audit | immutable event log (auto-captured via event bus) |
| analytics | analytics | spend aggregation |
| vendor_portal | vendor_portal | vendor portal event stream |
| payments | payments | payment runs (NEFT/RTGS/IMPS), individual payments, UTR |
| tds | tds | TDS deductions (Sec 194C/J/H/I/Q/A), challan, Form 16A |
| documents | documents | document metadata, versioning, checksums |

## Synthetic Data (Seeded)

### Suppliers (15 total, 5 MSME)

MSME suppliers: SUP003 (Rajesh Office, MICRO), SUP005 (Gujarat Tech, SMALL), SUP007 (Mumbai Print, MICRO), SUP009 (Suresh Traders, MICRO), SUP011 (Karnataka Tech, SMALL), SUP012 (Delhi Stationery Hub, MICRO -- 6 total MSME).

Non-MSME: SUP001 (TechMahindra), SUP002 (Wipro), SUP004 (ITC), SUP006 (Sodexo), SUP008 (Deloitte), SUP010 (Infosys BPM), SUP013 (HCL), SUP014 (KPMG), SUP015 (Compass India).

### Purchase Requests (8)

| ID | Title | Status | Dept |
|----|-------|--------|------|
| PR2024-001 | Cloud Infrastructure Upgrade | PO_CREATED | TECH |
| PR2024-002 | Annual Office Stationery Q3 | PO_CREATED | ADMIN |
| PR2024-003 | Security Audit & Pen Testing | APPROVED | FIN |
| PR2024-004 | Canteen & Pantry Supplies | PENDING_APPROVAL | ADMIN |
| PR2024-005 | Brand Collateral Print - Diwali | PENDING_APPROVAL | MKT |
| PR2024-006 | HR Training Platform License | APPROVED | HR |
| PR2024-007 | Data Center Rack Space | REJECTED | TECH |
| PR2024-008 | P2P Change Management Consulting | PO_CREATED | OPS |

### Purchase Orders (3) and GRNs (3)

| PO | PR | Supplier | Status |
|----|----|----------|--------|
| PO2024-001 | PR2024-001 | TechMahindra | RECEIVED (GRN complete) |
| PO2024-002 | PR2024-002 | Rajesh Office | PARTIALLY_RECEIVED (GRN partial) |
| PO2024-003 | PR2024-008 | KPMG India | RECEIVED (GRN partial -- 2/3 months hypercare) |

### Invoices (7) -- Key Scenarios

| ID | Scenario | Status | Supplier |
|----|----------|--------|----------|
| INV001 | Happy path -- 3-way matched, approved, posted to Oracle AP | POSTED_TO_EBS | TechMahindra |
| INV002 | MSME + 3-way match exception (partial GRN for pens) | PENDING_APPROVAL | Rajesh Office (MICRO) |
| INV003 | Fraud -- duplicate of INV001 (same invoice number) | REJECTED | TechMahindra |
| INV004 | Consulting -- clean match, pending approval | MATCHED | KPMG India |
| INV005 | MSME AT RISK -- 7 days remaining to 45-day limit | PENDING_APPROVAL | Gujarat Tech (SMALL) |
| INV006 | MSME BREACHED -- 7 days past limit, penalty accruing | APPROVED | Mumbai Print (MICRO) |
| INV007 | Just captured -- OCR not yet run | CAPTURED | Sodexo Facilities |

### Other Seed Data

- **15 GST cache records** (3 missing GSTR-2B, 1 GSTR-1 delayed)
- **8 Oracle EBS events** (3 PO commitments, 3 invoice posts, 1 GL journal, 1 FA addition; 1 failed for retry demo)
- **7 AI insights** covering all 5 agents
- **6 vendor portal events** (onboarding, bank verification, GSTIN update, document expiry)
- **6 budgets** (TECH, OPS, FIN, MKT, HR, ADMIN)

## Frontend Pages (18)

### Core P2P
| Page | Route | Component File |
|------|-------|---------------|
| Dashboard | `/dashboard` | `Dashboard.jsx` |
| Purchase Requests | `/purchase-requests` | `PurchaseRequests.jsx` |
| Purchase Orders | `/purchase-orders` | `PurchaseOrders.jsx` |
| Invoices | `/invoices` | `Invoices.jsx` |
| Invoice Detail | `/invoices/:id` | `InvoiceDetail.jsx` |
| Matching Engine | `/matching` | `Matching.jsx` |
| Payments | `/payments` | `Payments.jsx` |
| TDS Management | `/tds` | `TDSManagement.jsx` |

### Compliance
| Page | Route | Component File |
|------|-------|---------------|
| GST Cache | `/gst-cache` | `GSTCache.jsx` |
| MSME Compliance | `/msme` | `MSMECompliance.jsx` |
| Oracle EBS Sync | `/ebs` | `EBSIntegration.jsx` |

### Operations
| Page | Route | Component File |
|------|-------|---------------|
| Workflow | `/workflow` | `Workflow.jsx` |
| Documents | `/documents` | `Documents.jsx` |
| Notifications | `/notifications` | `Notifications.jsx` |
| Audit Trail | `/audit` | `AuditTrail.jsx` |

### Intelligence
| Page | Route | Component File |
|------|-------|---------------|
| AI Agents | `/ai-agents` | `AIAgents.jsx` |
| Spend Analytics | `/analytics` | `SpendAnalytics.jsx` |
| Suppliers | `/suppliers` | `Suppliers.jsx` |

## API Surface

75+ endpoints, all prefixed `/api/`. See `docs/API_REFERENCE.md` for full list.

Key endpoint groups: dashboard, suppliers, purchase-requests, purchase-orders, invoices, matching, payments, tds, documents, workflow, notifications, audit, gst-cache, msme-compliance, oracle-ebs, ai-agents, vendor-portal, analytics, budgets, health, auth.

## Indian Regulatory Requirements

| Requirement | Implementation |
|------------|---------------|
| GST / IRN | Cygnet GSP integration -- batch cache sync, live IRN/e-way bill calls |
| GSTR-2B reconciliation | Cached GSTR-2B data for ITC eligibility check |
| MSME Section 43B(h) | 45-day payment SLA tracking, breach detection, penalty calculation (3x RBI rate compound interest) |
| TDS | Deduction by vendor/category, Form 16A tracking |
| RBI audit trail | 7-year immutable event log retention |
| SAMADHAAN | MSME breach reporting integration (planned) |

## Key Development Rules

1. **Never put business logic in `routes.py`** -- use `service.py`.
2. **All inter-module communication through event bus** -- no direct imports.
3. **Keep API response shapes backward-compatible** with the existing frontend.
4. **Store money as integers (paise)** -- 1 INR = 100 paise.
5. **Human-readable codes** (`SUP001`, `PR2024-001`) as public API IDs.
6. **UUIDs are internal only** -- never expose to frontend.
7. **Every state change publishes an event**.
8. **Audit module logs ALL events**.

## Key Files

| File | Purpose |
|------|---------|
| `backend/main.py` | App factory, all routes (prototype), router mounting (modular) |
| `backend/config.py` | Settings via environment variables |
| `backend/database.py` | Async SQLAlchemy session factory |
| `backend/event_bus.py` | Internal async event bus |
| `backend/seed.py` | Synthetic data seeder |
| `frontend/src/api.js` | Frontend API client (all endpoint bindings) |
| `frontend/src/App.jsx` | React Router configuration |
| `frontend/vite.config.js` | Vite config with `/api` proxy to backend |
| `render.yaml` | Render.com deployment config |
| `Dockerfile` | Production container build |
| `CLAUDE.md` | Quick reference for AI assistants |

## Deployment

- **Local**: Vite dev server (5173) + FastAPI (8001) with Vite proxy. Start with: `uvicorn backend.main:app --port 8001`
- **Production**: Render.com -- single web service, React built into `frontend/dist/`, served by FastAPI as static files
- **Docker**: `Dockerfile` builds Python + pre-built frontend dist. Runs `uvicorn backend.main:app` from project root.
- **Important**: Always run uvicorn from the project root, not from inside `backend/`. The modular imports (`from backend.modules...`) require the project root in the Python path.
