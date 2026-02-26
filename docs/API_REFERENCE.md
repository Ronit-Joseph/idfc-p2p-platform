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

## Endpoint Summary

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
