# IDFC P2P Platform — Prototype

## Quick Start (2 terminals)

### Terminal 1 — Backend API
```
cd p2p\backend
python -m uvicorn main:app --reload --port 8000
```
API runs at: http://localhost:8000
Swagger docs: http://localhost:8000/docs

### Terminal 2 — Frontend UI
```
cd p2p\frontend
npm run dev
```
UI runs at: http://localhost:5173

Or use the .bat files:  double-click `start_backend.bat` then `start_frontend.bat`

---

## What's in the Prototype

| Page | URL | What it shows |
|---|---|---|
| Dashboard | /dashboard | KPIs, spend trend, MSME alerts, EBS failures, activity feed |
| Purchase Requests | /purchase-requests | Full PR lifecycle — create with live budget check, approve/reject |
| Purchase Orders | /purchase-orders | PO detail with line-item GRN match and EBS GL encumbrance status |
| Invoice Management | /invoices | Invoice list with GST cache badge, 3-way match, AI coding, MSME SLA |
| Invoice Detail | /invoices/INV002 | **Hero page** — all subsystems visible for one invoice |
| GST Cache | /gst-cache | Cygnet sync strategy, GSTIN registry, sync now button |
| MSME Compliance | /msme | SLA countdown per invoice, breach alerts, Sec 43B(h) penalty |
| Oracle EBS Sync | /ebs | Integration event log, scope of EBS retained vs decommissioned, retry |
| AI Agents | /ai-agents | 5 agents, confidence scores, reasoning traces, apply actions |
| Spend Analytics | /analytics | Stacked spend charts, budget vs actual, top vendors |
| Suppliers | /suppliers | Supplier registry, vendor portal event stream, risk scores |

---

## Interactive Actions to Try

1. **Create a PR** → go to Purchase Requests → New PR → type an amount and pick department → see live budget check
2. **Approve a PR** → click Approve on any PENDING_APPROVAL row
3. **Invoice INV002** → click to open — see 3-way match exception, MSME SLA, AI coding suggestion, EBS pending
4. **Invoice INV003** → fraud-blocked duplicate — see Fraud Agent reasoning
5. **Invoice INV005** → MSME AT RISK (7 days) — see SLA countdown
6. **Invoice INV006** → MSME BREACHED — see penalty amount accruing
7. **Approve an invoice** → opens Invoice Detail → click Approve → EBS posting event is created
8. **GST Cache → Sync from Cygnet** → simulates batch pull, updates timestamps, resolves some missing GSTR-2B
9. **EBS Integration → Retry failed** → EBS005 (failed AP posting) → click Retry → status flips to ACKNOWLEDGED
10. **AI Agents** → click Apply on any pending insight

---

## Synthetic Data Summary

- **15 suppliers** (5 MSME: Rajesh Office, Gujarat Tech, Mumbai Print, Suresh Traders, Karnataka Tech)
- **8 Purchase Requests** (all states: Draft → Approved → PO Created → Rejected)
- **3 Purchase Orders** with GRNs (one partial, one complete)
- **7 Invoices** demonstrating every scenario:
  - INV001: Happy path — 3-way matched, approved, posted to Oracle AP
  - INV002: MSME + 3-way match exception (partial GRN)
  - INV003: Fraud blocked — duplicate invoice
  - INV004: Consulting invoice, clean match, pending approval
  - INV005: MSME AT RISK — 7 days remaining to pay
  - INV006: MSME BREACHED — 7 days overdue, penalty ₹8,428
  - INV007: Just captured — shows OCR pending state
- **15 GSTINs** in cache (3 missing GSTR-2B, 1 GSTR-1 delayed)
- **8 Oracle EBS events** (1 failed AP posting for retry demo)
- **7 AI Agent insights** across all 5 agents
- **6 Vendor Portal events** (onboarding, bank verification, GSTIN update)
