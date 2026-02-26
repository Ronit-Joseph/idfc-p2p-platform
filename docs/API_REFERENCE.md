# IDFC P2P Platform -- API Reference

Base URL: `http://localhost:8000` (local dev) or deployment URL.

All endpoints are prefixed with `/api/`. Swagger UI is available at `/docs`.

---

## Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check with service and integration status |

**Response** (`GET /api/health`):
```json
{
  "status": "ok",
  "version": "0.1.0-prototype",
  "services": { "supplier_service": "UP", "invoice_service": "UP", ... },
  "integrations": { "oracle_ebs": "CONNECTED (AP, GL, FA)", ... }
}
```

---

## Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Authenticate and receive JWT token |
| GET | `/api/auth/me` | Get current user profile (requires JWT) |

**Request** (`POST /api/auth/login`):
```json
{ "email": "user@idfc.com", "password": "..." }
```

**Response**: JWT token + user profile.

---

## Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard` | Aggregated dashboard data |

**Response** (`GET /api/dashboard`):
```json
{
  "stats": {
    "invoices_pending": 3,
    "mtd_spend": 5552800,
    "mtd_spend_fmt": "₹55.5L",
    "active_pos": 3,
    "active_suppliers": 15,
    "prs_pending": 2,
    "msme_at_risk_count": 2,
    "ebs_failures": 1,
    "fraud_blocked": 1,
    "gst_cache_age_hours": 4.2,
    "gst_last_sync": "2024-09-25T..."
  },
  "alerts": [ { "type": "CRITICAL", "msg": "..." } ],
  "monthly_trend": [ { "month": "Apr", "spend": 14200000 } ],
  "spend_by_category": [ { "category": "IT Services", "amount": 28500000 } ],
  "activity": [ { "time": "...", "msg": "Invoice uploaded..." } ],
  "budget_utilization": [ { "dept": "Technology", "total": 80000000, ... } ]
}
```

---

## Suppliers

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/suppliers` | List all suppliers |
| GET | `/api/suppliers/{sid}` | Get supplier detail with GST data and recent invoices |

**Response** (`GET /api/suppliers`): Array of supplier objects.

**Response** (`GET /api/suppliers/{sid}`): Supplier object + `gst_data` (GST cache record) + `recent_invoices` (last 5 invoices).

---

## Purchase Requests

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/purchase-requests` | List all PRs |
| GET | `/api/purchase-requests/{pr_id}` | Get PR detail with budget info |
| POST | `/api/purchase-requests` | Create a new PR (with live budget check) |
| PATCH | `/api/purchase-requests/{pr_id}/approve` | Approve a pending PR |
| PATCH | `/api/purchase-requests/{pr_id}/reject` | Reject a pending PR |

**Request** (`POST /api/purchase-requests`):
```json
{
  "title": "New IT Equipment",
  "department": "TECH",
  "amount": 500000,
  "gl_account": "6100-003",
  "cost_center": "CC-TECH-01",
  "category": "IT Services",
  "justification": "Need new monitors",
  "requester": "John Doe"
}
```

**Response**: Created PR object with `budget_check` field (APPROVED or FAILED).

**Response** (`GET /api/purchase-requests/{pr_id}`): PR object + `budget` (current budget data for the PR's department).

**Approve/Reject**: Returns updated PR object. Approve only works on `PENDING_APPROVAL` status.

---

## Purchase Orders

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/purchase-orders` | List all POs |
| GET | `/api/purchase-orders/{po_id}` | Get PO detail with GRN, PR, and linked invoices |

**Response** (`GET /api/purchase-orders/{po_id}`): PO object + `grn` (GRN data) + `pr` (source PR) + `invoices` (linked invoices).

---

## Invoices

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/invoices` | List all invoices (optional `?status=` filter) |
| GET | `/api/invoices/{inv_id}` | Get invoice detail with all linked data |
| PATCH | `/api/invoices/{inv_id}/approve` | Approve an invoice (creates EBS posting event) |
| PATCH | `/api/invoices/{inv_id}/reject` | Reject an invoice |
| POST | `/api/invoices/{inv_id}/simulate-processing` | Step through processing pipeline |

**Query parameter** (`GET /api/invoices?status=PENDING_APPROVAL`): Filter by status.

**Response** (`GET /api/invoices/{inv_id}`): Invoice object enriched with:
- `supplier` -- full supplier record
- `gst_cache_data` -- GST cache record for supplier GSTIN
- `purchase_order` -- linked PO (if any)
- `grn` -- linked GRN (if any)
- `ai_insights` -- all AI insights for this invoice
- `ebs_events` -- all EBS events for this invoice

**Approve** (`PATCH /api/invoices/{inv_id}/approve`): Allowed from statuses MATCHED, PENDING_APPROVAL, VALIDATED. Sets status to APPROVED, creates an EBS INVOICE_POST event.

**Simulate Processing** (`POST /api/invoices/{inv_id}/simulate-processing`): Steps through the pipeline one stage at a time:
- CAPTURED --> EXTRACTED (OCR)
- EXTRACTED --> VALIDATED (GST validation)
- VALIDATED --> MATCHED (matching + AI coding)
- MATCHED --> PENDING_APPROVAL

---

## GST Cache

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/gst-cache` | Get all cached GST records with sync summary |
| GET | `/api/gst-cache/{gstin}` | Get a specific GSTIN record |
| POST | `/api/gst-cache/sync` | Trigger a Cygnet batch sync |

**Response** (`GET /api/gst-cache`):
```json
{
  "records": [ { "gstin": "27AATCM5678P1ZS", ... } ],
  "last_full_sync": "2024-09-25T...",
  "total": 15,
  "active": 15,
  "gstr2b_available": 12,
  "gstr2b_missing": 3,
  "gstr1_delayed": 1,
  "total_cache_hits": 241,
  "live_calls_avoided": 241,
  "sync_provider": "Cygnet GSP"
}
```

**Response** (`POST /api/gst-cache/sync`):
```json
{
  "status": "SYNC_COMPLETE",
  "synced_at": "...",
  "provider": "Cygnet GSP",
  "records_updated": 2,
  "total_gstins": 15,
  "batch_type": "INCREMENTAL"
}
```

---

## MSME Compliance

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/msme-compliance` | Get MSME compliance dashboard with SLA tracking |

**Response** (`GET /api/msme-compliance`):
```json
{
  "summary": {
    "total_msme_invoices": 3,
    "on_track": 1,
    "at_risk": 1,
    "breached": 1,
    "total_pending_msme_amount": 1050800,
    "total_penalty_accrued": 8428,
    "section_43bh": "Section 43B(h) -- Finance Act 2023",
    "max_payment_days": 45,
    "rbi_rate": 6.5,
    "penalty_multiplier": 3
  },
  "invoices": [
    {
      "invoice_id": "INV002",
      "msme_category": "MICRO",
      "days_remaining": 24,
      "msme_status": "ON_TRACK",
      "risk_level": "GREEN"
    }
  ]
}
```

---

## Oracle EBS Integration

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/oracle-ebs/events` | List all EBS integration events with summary |
| POST | `/api/oracle-ebs/events/{event_id}/retry` | Retry a failed EBS event |

**Response** (`GET /api/oracle-ebs/events`):
```json
{
  "events": [ { "id": "EBS001", "event_type": "PO_COMMITMENT", ... } ],
  "summary": { "total": 8, "acknowledged": 5, "pending": 2, "failed": 1 },
  "ebs_modules_active": ["AP", "GL", "FA"],
  "ebs_modules_retired": ["PR", "PO", "Invoice UI"],
  "integration_method": "Oracle Integration Cloud (OIC)"
}
```

**Retry** (`POST /api/oracle-ebs/events/{event_id}/retry`): Only works on FAILED events. Flips status to ACKNOWLEDGED, assigns EBS reference, and updates linked invoice status.

---

## AI Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/ai-agents/insights` | List all AI insights and agent configs |
| POST | `/api/ai-agents/insights/{insight_id}/apply` | Apply a pending AI insight |

**Response** (`GET /api/ai-agents/insights`):
```json
{
  "insights": [ { "id": "AI001", "agent": "InvoiceCodingAgent", ... } ],
  "agents": [
    {
      "name": "InvoiceCodingAgent",
      "status": "ACTIVE",
      "model": "fine-tuned-bert-v2.1",
      "avg_confidence": 91.2,
      "invoices_coded_mtd": 23
    }
  ]
}
```

**Apply** (`POST /api/ai-agents/insights/{insight_id}/apply`): Sets `applied: true`, `status: "APPLIED"`, and records `applied_at` timestamp.

---

## Vendor Portal Events

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/vendor-portal/events` | List all vendor portal events |

**Response**: Array of vendor portal event objects with `event_type`, `supplier_id`, `payload`, `processed`, and `p2p_action`.

---

## Spend Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/spend` | Get spend analytics and KPIs |

**Response** (`GET /api/analytics/spend`):
```json
{
  "spend_by_category": [ { "category": "IT Services", "amount": 28500000 } ],
  "monthly_trend": [ { "month": "Apr 24", "it": 5200000, "consulting": 3100000 } ],
  "top_vendors": [ { "name": "TechMahindra", "amount": 12400000 } ],
  "budget_vs_actual": [ { "dept": "Technology", "budget": 80000000 } ],
  "kpis": {
    "invoice_cycle_time_days": 4.2,
    "three_way_match_rate_pct": 81.4,
    "auto_approval_rate_pct": 34.2,
    "early_payment_savings_mtd": 87500,
    "maverick_spend_pct": 6.3,
    "po_coverage_pct": 73.8
  }
}
```

---

## Budgets

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/budgets` | List all department budgets |
| POST | `/api/budgets/check?dept={code}&amount={value}` | Check budget availability |

**Response** (`POST /api/budgets/check?dept=TECH&amount=500000`):
```json
{
  "dept": "TECH",
  "dept_name": "Technology",
  "requested_amount": 500000,
  "available_amount": 28000000,
  "total_budget": 80000000,
  "committed": 22000000,
  "actual": 30000000,
  "status": "APPROVED",
  "utilization_after_pct": 65.6
}
```

Status is `APPROVED` if `amount <= available`, otherwise `INSUFFICIENT`.

---

## Workflow / Approvals

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/workflow/matrices` | List all approval matrix rules |
| POST | `/api/workflow/matrices` | Create an approval rule |
| GET | `/api/workflow/pending` | List pending approval instances (optional `?approver_role=`) |
| POST | `/api/workflow/request` | Create approval request (auto-determines levels from matrix) |
| GET | `/api/workflow/approvals/{id}` | Get approval instance with steps |
| GET | `/api/workflow/approvals/entity/{type}/{id}` | Get approvals for a specific entity |
| POST | `/api/workflow/approvals/{id}/approve` | Approve current step |
| POST | `/api/workflow/approvals/{id}/reject` | Reject (cancels remaining steps) |

---

## Matching Engine

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/matching/results` | List all match results |
| GET | `/api/matching/summary` | Match statistics (passed, exceptions, blocked) |
| POST | `/api/matching/run` | Run 2WAY or 3WAY match on an invoice |
| GET | `/api/matching/exceptions` | List matching exceptions |
| POST | `/api/matching/exceptions/{id}/resolve` | Resolve exception (APPROVED_OVERRIDE/REJECTED/ESCALATED) |

---

## Payments

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/payments` | List all individual payments |
| GET | `/api/payments/summary` | Payment totals and status breakdown |
| GET | `/api/payments/runs` | List payment runs with nested payments |
| POST | `/api/payments/runs` | Create a payment run for approved invoices |
| POST | `/api/payments/runs/{id}/process` | Advance run (DRAFT->SCHEDULED->PROCESSING->COMPLETED) |

---

## TDS Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tds` | List all TDS deductions |
| GET | `/api/tds/summary` | TDS totals, pending deposits, Form 16A status |
| GET | `/api/tds/rates` | TDS rate card (all sections with individual/company rates) |
| POST | `/api/tds` | Create TDS deduction (auto-calculates with 4% H&E cess) |
| POST | `/api/tds/{id}/deposit` | Record challan deposit |
| POST | `/api/tds/{id}/form16a` | Generate Form 16A certificate |

---

## Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/documents` | List documents (optional `?entity_type=&entity_id=&document_type=`) |
| GET | `/api/documents/summary` | Document counts by entity/type, total size |
| GET | `/api/documents/entity/{type}/{id}` | Get all documents for a specific entity |
| POST | `/api/documents` | Register document metadata (auto-version, SHA-256 checksum) |
| DELETE | `/api/documents/{id}` | Soft-delete a document |

---

## Notifications

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/notifications` | List notifications (optional `?unread_only=true&limit=50`) |
| GET | `/api/notifications/unread-count` | Get count of unread notifications |
| POST | `/api/notifications` | Create a notification (admin/system use) |
| PATCH | `/api/notifications/{id}/read` | Mark single notification as read |
| POST | `/api/notifications/mark-all-read` | Mark all notifications as read |

---

## Audit Trail

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/audit` | List audit logs (optional `?source_module=&event_type=&entity_type=&entity_id=`) |
| GET | `/api/audit/summary` | Event counts by module, by type, last 24h |
| GET | `/api/audit/entity/{type}/{id}` | Full audit trail for a specific entity |

---

## Endpoint Summary (75+ endpoints)

### Core P2P (30 endpoints)
| # | Method | Endpoint | Module |
|---|--------|----------|--------|
| 1 | GET | `/api/health` | health |
| 2 | POST | `/api/auth/login` | auth |
| 3 | GET | `/api/auth/me` | auth |
| 4 | GET | `/api/dashboard` | dashboard |
| 5 | GET | `/api/suppliers` | suppliers |
| 6 | GET | `/api/suppliers/{sid}` | suppliers |
| 7 | GET | `/api/purchase-requests` | purchase_requests |
| 8 | GET | `/api/purchase-requests/{pr_id}` | purchase_requests |
| 9 | POST | `/api/purchase-requests` | purchase_requests |
| 10 | PATCH | `/api/purchase-requests/{pr_id}/approve` | purchase_requests |
| 11 | PATCH | `/api/purchase-requests/{pr_id}/reject` | purchase_requests |
| 12 | GET | `/api/purchase-orders` | purchase_orders |
| 13 | GET | `/api/purchase-orders/{po_id}` | purchase_orders |
| 14 | GET | `/api/invoices` | invoices |
| 15 | GET | `/api/invoices/{inv_id}` | invoices |
| 16 | PATCH | `/api/invoices/{inv_id}/approve` | invoices |
| 17 | PATCH | `/api/invoices/{inv_id}/reject` | invoices |
| 18 | POST | `/api/invoices/{inv_id}/simulate-processing` | invoices |
| 19 | GET | `/api/gst-cache` | gst_cache |
| 20 | GET | `/api/gst-cache/{gstin}` | gst_cache |
| 21 | POST | `/api/gst-cache/sync` | gst_cache |
| 22 | GET | `/api/msme-compliance` | msme_compliance |
| 23 | GET | `/api/oracle-ebs/events` | ebs_integration |
| 24 | POST | `/api/oracle-ebs/events/{event_id}/retry` | ebs_integration |
| 25 | GET | `/api/ai-agents/insights` | ai_agents |
| 26 | POST | `/api/ai-agents/insights/{insight_id}/apply` | ai_agents |
| 27 | GET | `/api/vendor-portal/events` | vendor_portal |
| 28 | GET | `/api/analytics/spend` | analytics |
| 29 | GET | `/api/budgets` | budgets |
| 30 | POST | `/api/budgets/check` | budgets |

### Sprint 4 Enterprise Modules (45 endpoints)
| # | Method | Endpoint | Module |
|---|--------|----------|--------|
| 31 | GET | `/api/workflow/matrices` | workflow |
| 32 | POST | `/api/workflow/matrices` | workflow |
| 33 | GET | `/api/workflow/pending` | workflow |
| 34 | POST | `/api/workflow/request` | workflow |
| 35 | GET | `/api/workflow/approvals/{id}` | workflow |
| 36 | GET | `/api/workflow/approvals/entity/{type}/{id}` | workflow |
| 37 | POST | `/api/workflow/approvals/{id}/approve` | workflow |
| 38 | POST | `/api/workflow/approvals/{id}/reject` | workflow |
| 39 | GET | `/api/matching/results` | matching |
| 40 | GET | `/api/matching/summary` | matching |
| 41 | POST | `/api/matching/run` | matching |
| 42 | GET | `/api/matching/exceptions` | matching |
| 43 | POST | `/api/matching/exceptions/{id}/resolve` | matching |
| 44 | GET | `/api/payments` | payments |
| 45 | GET | `/api/payments/summary` | payments |
| 46 | GET | `/api/payments/runs` | payments |
| 47 | POST | `/api/payments/runs` | payments |
| 48 | POST | `/api/payments/runs/{id}/process` | payments |
| 49 | GET | `/api/tds` | tds |
| 50 | GET | `/api/tds/summary` | tds |
| 51 | GET | `/api/tds/rates` | tds |
| 52 | POST | `/api/tds` | tds |
| 53 | POST | `/api/tds/{id}/deposit` | tds |
| 54 | POST | `/api/tds/{id}/form16a` | tds |
| 55 | GET | `/api/documents` | documents |
| 56 | GET | `/api/documents/summary` | documents |
| 57 | GET | `/api/documents/entity/{type}/{id}` | documents |
| 58 | POST | `/api/documents` | documents |
| 59 | DELETE | `/api/documents/{id}` | documents |
| 60 | GET | `/api/notifications` | notifications |
| 61 | GET | `/api/notifications/unread-count` | notifications |
| 62 | POST | `/api/notifications` | notifications |
| 63 | PATCH | `/api/notifications/{id}/read` | notifications |
| 64 | POST | `/api/notifications/mark-all-read` | notifications |
| 65 | GET | `/api/audit` | audit |
| 66 | GET | `/api/audit/summary` | audit |
| 67 | GET | `/api/audit/entity/{type}/{id}` | audit |

---

## Error Responses

All errors follow this format:

```json
{ "detail": "Error message describing what went wrong" }
```

| Status Code | Meaning |
|-------------|---------|
| 400 | Bad request (e.g., invalid state transition) |
| 404 | Resource not found |
| 422 | Validation error (missing/invalid request body fields) |
| 500 | Internal server error |
