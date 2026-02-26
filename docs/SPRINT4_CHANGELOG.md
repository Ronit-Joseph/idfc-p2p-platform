# Sprint 4: Enterprise Features -- Changelog

**Version**: 0.5.0
**Commits**: `99d6b0b` (backend), `4c6bd95` (frontend UI), `fe36abb` (deploy fix)

---

## Summary

Sprint 4 added 7 critical enterprise modules (backend + frontend) to close the gap between the prototype and industry-standard P2P platforms like SAP Ariba, Coupa, and Oracle Procurement Cloud. Total system now has **75+ API endpoints** and **18 frontend pages** across **19 modules**.

---

## New Backend Modules (7)

### 1. Workflow Engine (`/api/workflow` -- 8 endpoints)
Multi-level approval engine with configurable approval matrices.

- **Approval Matrix**: Rules define approver role, level, amount range, department, entity type
- **Auto-level detection**: `POST /api/workflow/request` reads matrix rules and creates the correct number of approval steps
- **Step-by-step approval**: Each level must be approved before the next activates
- **Rejection cascade**: Rejecting any step cancels all remaining steps
- **Seeded data**: 9 matrix rules (PR: 3 amount tiers x 3 levels, Invoice: 2 tiers x 2 levels)

### 2. Matching Engine (`/api/matching` -- 5 endpoints)
2-way and 3-way invoice matching with fraud detection.

- **2WAY match**: PO amount vs Invoice amount (5% tolerance)
- **3WAY match**: PO + GRN quantity + Invoice amount
- **Fraud blocking**: Invoices flagged by AI FraudDetectionAgent are auto-blocked
- **Exception queue**: Mismatches create exceptions with CRITICAL/HIGH/MEDIUM/LOW severity
- **Resolution**: Exceptions can be APPROVED_OVERRIDE, REJECTED, or ESCALATED

### 3. Payment Processing (`/api/payments` -- 5 endpoints)
Bank payment runs with TDS auto-deduction and UTR tracking.

- **Payment runs**: Batch processing of approved invoices (NEFT/RTGS/IMPS)
- **Lifecycle**: DRAFT -> SCHEDULED -> PROCESSING -> COMPLETED
- **TDS deduction**: Auto-deducted per supplier TDS configuration
- **Bank file reference**: Generated on processing (format: `{METHOD}-{RUN}-{DATE}`)
- **UTR tracking**: Bank reference (UTR) recorded per individual payment

### 4. TDS Management (`/api/tds` -- 6 endpoints)
Indian Tax Deducted at Source compliance.

- **6 sections supported**: 194C (contractors), 194J (professional), 194H (commission), 194I (rent), 194Q (purchase of goods), 194A (interest)
- **Auto-calculation**: TDS amount + 4% Health & Education Cess
- **Rate card**: Individual vs Company rates per section
- **Challan tracking**: Deposit date, BSR code, challan number
- **Form 16A**: Certificate generation and tracking

### 5. Document Management (`/api/documents` -- 5 endpoints)
Document metadata tracking with versioning and checksums.

- **Entity association**: Documents linked to invoices, POs, GRNs, suppliers, contracts
- **Auto-versioning**: Version increments for same entity + document type
- **SHA-256 checksums**: Integrity verification
- **Soft delete**: `is_active` flag preserves audit trail
- **Seeded data**: 5 documents (2 invoice PDFs, 1 PO copy, 1 GRN photo, 1 tax certificate)

### 6. Notifications (`/api/notifications` -- 5 endpoints)
Centralized alert system with severity-based prioritization.

- **Severity levels**: CRITICAL, HIGH (previously WARNING), MEDIUM, LOW, INFO
- **Notification types**: MSME_ALERT, FRAUD_WARNING, APPROVAL_REQUEST, EBS_FAILURE, GST_ISSUE
- **Read tracking**: Mark individual or all notifications as read
- **Unread count**: Separate endpoint for badge display
- **Seeded data**: 6 notifications covering all severity levels

### 7. Audit Trail (`/api/audit` -- 3 endpoints)
Immutable event log with automatic capture via event bus.

- **Auto-capture**: ALL event bus events are persisted to audit_logs table via `_audit_event()` handler
- **24 event types subscribed**: From workflow, matching, payments, TDS, invoices, purchase requests, etc.
- **Filterable**: By source_module, event_type, entity_type, entity_id
- **Summary**: Counts by module, by event type, last 24 hours
- **7-year retention**: Designed for RBI compliance

---

## New Frontend Pages (7)

### 1. Payments (`/payments`)
- Summary cards: total payments, total disbursed, pending, completed
- Two tabs: Payment Runs (with advance/process button) and Individual Payments
- Columns: payment number, invoice, supplier, amount, TDS deducted, net amount, UTR, status

### 2. TDS Management (`/tds`)
- Summary cards: total deductions, TDS amount, deposited, Form 16A pending
- Two tabs: Deductions table and TDS Rate Card
- Section badges with color coding (194C blue, 194J purple, etc.)
- Rate card shows individual vs company rates per section

### 3. Documents (`/documents`)
- Summary cards: total documents, total size, entity types, doc types
- Entity type breakdown chips
- Filterable by entity type
- Table with file icon, name, entity, version badge, size, uploaded by

### 4. Workflow (`/workflow`)
- Summary cards: pending, approved, rejected, total rules
- Two tabs: Approval Instances and Approval Matrix Rules
- Expandable instances showing each approval step with level badges
- Approve/Reject buttons on pending instances

### 5. Matching Engine (`/matching`)
- Summary cards: total matches, passed, exceptions, blocked fraud, open exceptions
- Two tabs: Match Results and Exceptions
- Variance % with color coding (green < 0%, yellow < 5%, red > 5%)
- Exception resolution buttons: Override, Reject, Escalate

### 6. Audit Trail (`/audit`)
- Summary cards: total events, last 24h, active modules, event types
- Module breakdown as clickable filter chips
- Entity search input
- Event table with type icon, module badge, entity, actor, timestamp

### 7. Notifications (`/notifications`)
- Summary cards: total, unread, critical, high priority
- Filter buttons: All, Unread, Critical, High, Medium, Low
- Severity-based card styling with left border color
- Mark Read button per notification, Mark All Read in header
- Bell icon in header now links to this page

---

## Infrastructure Changes

- **Sidebar**: Reorganized into 4 groups (Core P2P, Compliance, Operations, Intelligence) with 20 nav items
- **API client**: 30+ new API functions in `frontend/src/api.js`
- **Event bus -> Audit**: `_audit_event()` handler opens its own async session and persists all events
- **Seed data**: Approval matrices (9 rules), notifications (6), documents (5) added to `backend/seed.py`
- **Dockerfile**: Fixed to run from project root (`uvicorn backend.main:app`)
- **render.yaml**: Fixed start command to use `backend.main:app`

---

## Database Tables Added

| Table | Module | Key Fields |
|-------|--------|-----------|
| `approval_instances` | workflow | entity_type, entity_id, total_levels, current_level, status |
| `approval_steps` | workflow | instance_id FK, level, approver_role, status, comments |
| `matching_exceptions` | matching | match_result_id FK, exception_type, severity, resolution |
| `payment_runs` | payments | run_number, payment_method, status, bank_file_ref |
| `payments` | payments | payment_number, invoice_id FK, amount, tds_deducted, net_amount, UTR |
| `tds_deductions` | tds | section, tds_rate, base_amount, tds_amount, cess, challan tracking |
| `documents` | documents | entity_type, entity_id, file_name, version, checksum, is_active |

---

## Git History

```
fe36abb Fix Dockerfile and render.yaml: run uvicorn from project root
4c6bd95 Sprint 4 UI: Frontend pages for all 7 new backend modules
99d6b0b Sprint 4: Enterprise features -- workflow, audit, matching, payments, TDS, documents, notifications
a7d6998 Sprint 3: Invoice & Compliance -- all modules fully DB-backed
4eded86 Sprint 2: Core P2P -- budgets, PRs, POs, GRNs migrated to DB
a5790c2 Sprint 1: Foundation -- modular monolith architecture with DB-backed auth & suppliers
```
