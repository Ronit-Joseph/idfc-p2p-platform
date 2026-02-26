# IDFC P2P Platform -- Data Model

## Conventions

- **Primary keys**: UUIDs (internal only, never exposed to frontend)
- **Business identifiers**: Human-readable codes (`SUP001`, `PR2024-001`, `PO2024-001`, `INV001`) used in all API responses
- **Monetary amounts**: Stored as **integers in paise** (1 INR = 100 paise). Example: INR 45,000.00 is stored as `4500000`
- **Timestamps**: UTC, stored as `TIMESTAMP WITH TIME ZONE`
- **Soft deletes**: `is_deleted` boolean + `deleted_at` timestamp (no hard deletes)
- **Schema isolation**: Each module owns its own PostgreSQL schema

## Schema Overview

| Schema | Module(s) | Tables |
|--------|-----------|--------|
| `auth` | auth | users, roles, user_roles, sessions |
| `suppliers` | suppliers | suppliers |
| `budgets` | budgets | budgets, budget_encumbrances |
| `procurement` | purchase_requests, purchase_orders | purchase_requests, pr_line_items, purchase_orders, po_line_items, goods_receipt_notes, grn_line_items |
| `invoices` | invoices, matching, msme_compliance | invoices, invoice_line_items, match_results, msme_tracking |
| `gst` | gst_cache | gst_records, gst_sync_logs |
| `ebs` | ebs_integration | ebs_events |
| `ai` | ai_agents | ai_insights, ai_agent_configs |
| `workflow` | workflow | approval_matrices, approval_steps |
| `notifications` | notifications | notifications |
| `audit` | audit | audit_logs |
| `vendor_portal` | vendor_portal | vendor_portal_events |

---

## Table Definitions by Schema

### Schema: `auth`

#### users

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Internal identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Login email |
| name | VARCHAR(255) | NOT NULL | Display name |
| password_hash | VARCHAR(255) | NOT NULL | Bcrypt hash |
| role | VARCHAR(50) | NOT NULL | Primary role |
| department | VARCHAR(50) | | Department code (TECH, OPS, FIN, MKT, HR, ADMIN) |
| is_active | BOOLEAN | DEFAULT TRUE | Account active flag |
| created_at | TIMESTAMPTZ | NOT NULL | Account creation time |
| last_login_at | TIMESTAMPTZ | | Last successful login |

### Schema: `suppliers`

#### suppliers

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Internal identifier |
| code | VARCHAR(20) | UNIQUE, NOT NULL | Business ID (e.g., SUP001) |
| legal_name | VARCHAR(500) | NOT NULL | Registered legal name |
| gstin | VARCHAR(15) | UNIQUE | GST Identification Number |
| pan | VARCHAR(10) | | PAN number |
| state | VARCHAR(100) | | Registration state |
| category | VARCHAR(100) | | Business category |
| is_msme | BOOLEAN | DEFAULT FALSE | MSME registered flag |
| msme_category | VARCHAR(20) | | MICRO, SMALL, or MEDIUM |
| bank_account | VARCHAR(50) | | Masked bank account number |
| bank_name | VARCHAR(200) | | Bank name |
| ifsc | VARCHAR(11) | | IFSC code |
| payment_terms | INTEGER | DEFAULT 30 | Payment terms in days |
| risk_score | DECIMAL(3,1) | | AI-computed risk score (0-10) |
| status | VARCHAR(20) | NOT NULL | ACTIVE, INACTIVE, BLOCKED |
| vendor_portal_status | VARCHAR(30) | | VERIFIED, PENDING_VERIFICATION |
| contact_email | VARCHAR(255) | | Primary contact email |
| onboarded_date | DATE | | Date onboarded to platform |
| last_synced_from_portal | TIMESTAMPTZ | | Last sync from vendor portal |
| created_at | TIMESTAMPTZ | NOT NULL | Record creation time |
| updated_at | TIMESTAMPTZ | | Last update time |

### Schema: `budgets`

#### budgets

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Internal identifier |
| dept | VARCHAR(10) | UNIQUE, NOT NULL | Department code |
| dept_name | VARCHAR(100) | NOT NULL | Department display name |
| gl_account | VARCHAR(20) | NOT NULL | GL account number |
| cost_center | VARCHAR(20) | NOT NULL | Cost center code |
| fiscal_year | VARCHAR(20) | NOT NULL | Fiscal year (e.g., FY2024-25) |
| total | BIGINT | NOT NULL | Total budget (paise) |
| committed | BIGINT | DEFAULT 0 | Committed/encumbered amount (paise) |
| actual | BIGINT | DEFAULT 0 | Actual spent (paise) |
| available | BIGINT | NOT NULL | Available budget (paise) |
| currency | VARCHAR(3) | DEFAULT 'INR' | Currency code |

### Schema: `procurement`

#### purchase_requests

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Internal identifier |
| pr_number | VARCHAR(20) | UNIQUE, NOT NULL | Business ID (e.g., PR2024-001) |
| title | VARCHAR(500) | NOT NULL | PR title/description |
| department | VARCHAR(10) | NOT NULL | Department code |
| requester | VARCHAR(255) | NOT NULL | Requester name |
| requester_email | VARCHAR(255) | | Requester email |
| amount | BIGINT | NOT NULL | Total amount (paise) |
| currency | VARCHAR(3) | DEFAULT 'INR' | Currency code |
| gl_account | VARCHAR(20) | | GL account |
| cost_center | VARCHAR(20) | | Cost center |
| category | VARCHAR(100) | | Spend category |
| supplier_preference | VARCHAR(20) | FK (suppliers.code) | Preferred supplier code |
| justification | TEXT | | Business justification |
| status | VARCHAR(30) | NOT NULL | DRAFT, PENDING_APPROVAL, APPROVED, REJECTED, PO_CREATED |
| po_id | VARCHAR(20) | | Linked PO number |
| budget_check | VARCHAR(20) | | APPROVED, FAILED |
| budget_available_at_time | BIGINT | | Budget available when checked (paise) |
| approver | VARCHAR(255) | | Approver name |
| approved_at | TIMESTAMPTZ | | Approval timestamp |
| rejected_at | TIMESTAMPTZ | | Rejection timestamp |
| rejection_reason | TEXT | | Reason for rejection |
| created_at | TIMESTAMPTZ | NOT NULL | Creation time |

#### pr_line_items

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Internal identifier |
| pr_id | UUID | FK (purchase_requests.id), NOT NULL | Parent PR |
| description | VARCHAR(500) | NOT NULL | Item description |
| quantity | DECIMAL(12,3) | NOT NULL | Quantity |
| unit | VARCHAR(20) | NOT NULL | Unit of measure (PCS, KG, LS, REAM, etc.) |
| unit_price | BIGINT | NOT NULL | Unit price (paise) |
| total | BIGINT | NOT NULL | Line total (paise) |

#### purchase_orders

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Internal identifier |
| po_number | VARCHAR(20) | UNIQUE, NOT NULL | Business ID (e.g., PO2024-001) |
| pr_id | VARCHAR(20) | NOT NULL | Source PR number |
| supplier_id | VARCHAR(20) | NOT NULL | Supplier code |
| supplier_name | VARCHAR(500) | | Supplier name (denormalized) |
| amount | BIGINT | NOT NULL | Total PO amount (paise) |
| currency | VARCHAR(3) | DEFAULT 'INR' | Currency code |
| status | VARCHAR(30) | NOT NULL | ISSUED, ACKNOWLEDGED, PARTIALLY_RECEIVED, RECEIVED, CLOSED |
| delivery_date | DATE | | Expected/actual delivery date |
| dispatch_date | TIMESTAMPTZ | | Dispatch date |
| acknowledged_date | TIMESTAMPTZ | | Vendor acknowledgement date |
| grn_id | VARCHAR(20) | | Linked GRN number |
| ebs_commitment_status | VARCHAR(20) | | POSTED, PENDING, FAILED |
| ebs_commitment_ref | VARCHAR(50) | | EBS GL encumbrance reference |
| created_at | TIMESTAMPTZ | NOT NULL | Creation time |

#### po_line_items

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Internal identifier |
| po_id | UUID | FK (purchase_orders.id), NOT NULL | Parent PO |
| description | VARCHAR(500) | NOT NULL | Item description |
| quantity | DECIMAL(12,3) | NOT NULL | Ordered quantity |
| unit | VARCHAR(20) | NOT NULL | Unit of measure |
| unit_price | BIGINT | NOT NULL | Unit price (paise) |
| total | BIGINT | NOT NULL | Line total (paise) |
| grn_qty | DECIMAL(12,3) | DEFAULT 0 | GRN-confirmed quantity |

#### goods_receipt_notes

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Internal identifier |
| grn_number | VARCHAR(20) | UNIQUE, NOT NULL | Business ID (e.g., GRN2024-001) |
| po_id | VARCHAR(20) | NOT NULL | Parent PO number |
| received_date | DATE | NOT NULL | Date goods received |
| received_by | VARCHAR(255) | NOT NULL | Receiver name |
| status | VARCHAR(20) | NOT NULL | COMPLETE, PARTIAL |
| notes | TEXT | | Receipt notes |
| created_at | TIMESTAMPTZ | NOT NULL | Creation time |

#### grn_line_items

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Internal identifier |
| grn_id | UUID | FK (goods_receipt_notes.id), NOT NULL | Parent GRN |
| description | VARCHAR(500) | NOT NULL | Item description |
| po_qty | DECIMAL(12,3) | NOT NULL | Quantity on PO |
| received_qty | DECIMAL(12,3) | NOT NULL | Quantity received |
| unit | VARCHAR(20) | NOT NULL | Unit of measure |

### Schema: `invoices`

#### invoices

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Internal identifier |
| invoice_code | VARCHAR(20) | UNIQUE, NOT NULL | Internal code (e.g., INV001) |
| invoice_number | VARCHAR(100) | NOT NULL | Vendor's invoice number |
| supplier_id | VARCHAR(20) | NOT NULL | Supplier code |
| supplier_name | VARCHAR(500) | | Supplier name (denormalized) |
| po_id | VARCHAR(20) | | Linked PO number (nullable for non-PO invoices) |
| grn_id | VARCHAR(20) | | Linked GRN number |
| invoice_date | DATE | NOT NULL | Invoice date |
| due_date | DATE | NOT NULL | Payment due date |
| subtotal | BIGINT | NOT NULL | Pre-tax amount (paise) |
| gst_rate | DECIMAL(5,2) | | GST rate percentage |
| gst_amount | BIGINT | | GST amount (paise) |
| tds_rate | DECIMAL(5,2) | | TDS rate percentage |
| tds_amount | BIGINT | | TDS amount (paise) |
| total_amount | BIGINT | NOT NULL | Gross total (paise) |
| net_payable | BIGINT | NOT NULL | Net payable after TDS (paise) |
| gstin_supplier | VARCHAR(15) | | Supplier GSTIN |
| gstin_buyer | VARCHAR(15) | | Buyer (IDFC) GSTIN |
| hsn_sac | VARCHAR(10) | | HSN/SAC code |
| irn | VARCHAR(64) | | Invoice Reference Number (e-invoice) |
| status | VARCHAR(30) | NOT NULL | CAPTURED, EXTRACTED, VALIDATED, MATCHED, PENDING_APPROVAL, APPROVED, REJECTED, POSTED_TO_EBS, PAID |
| ocr_confidence | DECIMAL(5,1) | | OCR extraction confidence % |
| gstin_cache_status | VARCHAR(20) | | ACTIVE, INACTIVE, NOT_FOUND |
| gstin_validated_from_cache | BOOLEAN | | Whether GSTIN was validated from cache |
| gstr2b_itc_eligible | BOOLEAN | | ITC eligibility from GSTR-2B |
| gstin_cache_age_hours | DECIMAL(6,1) | | Age of cached GSTIN data in hours |
| match_status | VARCHAR(30) | | PENDING, 2WAY_MATCH_PASSED, 3WAY_MATCH_PASSED, 3WAY_MATCH_EXCEPTION, BLOCKED_FRAUD |
| match_variance | DECIMAL(5,1) | | Match variance percentage |
| match_exception_reason | TEXT | | Reason for match exception |
| coding_agent_gl | VARCHAR(20) | | AI-suggested GL account |
| coding_agent_confidence | DECIMAL(5,1) | | AI coding confidence % |
| coding_agent_category | VARCHAR(100) | | AI-suggested spend category |
| fraud_flag | BOOLEAN | DEFAULT FALSE | Flagged as fraudulent |
| fraud_reasons | JSONB | | Array of fraud reasons |
| cash_opt_suggestion | TEXT | | Cash optimization suggestion |
| ebs_ap_status | VARCHAR(20) | | NOT_STARTED, PENDING, POSTED, FAILED, BLOCKED |
| ebs_ap_ref | VARCHAR(50) | | EBS AP posting reference |
| ebs_posted_at | TIMESTAMPTZ | | EBS posting timestamp |
| approved_by | VARCHAR(255) | | Approver name |
| approved_at | TIMESTAMPTZ | | Approval timestamp |
| rejected_by | VARCHAR(255) | | Rejector name or agent |
| rejected_at | TIMESTAMPTZ | | Rejection timestamp |
| rejection_reason | TEXT | | Rejection reason |
| is_msme_supplier | BOOLEAN | DEFAULT FALSE | Whether supplier is MSME |
| msme_category | VARCHAR(20) | | MICRO, SMALL, MEDIUM |
| msme_days_remaining | INTEGER | | Days to 45-day MSME limit |
| msme_due_date | DATE | | MSME payment due date |
| msme_status | VARCHAR(20) | | ON_TRACK, AT_RISK, BREACHED |
| msme_penalty_amount | BIGINT | | Penalty amount (paise) |
| uploaded_by | VARCHAR(255) | | Who uploaded the invoice |
| created_at | TIMESTAMPTZ | NOT NULL | Creation time |
| updated_at | TIMESTAMPTZ | | Last update time |

### Schema: `gst`

#### gst_records

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Internal identifier |
| gstin | VARCHAR(15) | UNIQUE, NOT NULL | GST Identification Number |
| legal_name | VARCHAR(500) | NOT NULL | Registered legal name |
| status | VARCHAR(20) | NOT NULL | ACTIVE, INACTIVE, CANCELLED, SUSPENDED |
| state | VARCHAR(100) | | Registration state |
| registration_type | VARCHAR(50) | | Regular, Composition, etc. |
| last_gstr1_filed | VARCHAR(20) | | Last GSTR-1 filing period |
| gstr2b_available | BOOLEAN | | Whether GSTR-2B data is available |
| gstr2b_period | VARCHAR(20) | | GSTR-2B available period |
| gstr1_compliance | VARCHAR(20) | | FILED, PENDING, DELAYED |
| itc_eligible | BOOLEAN | | ITC eligibility |
| last_synced | TIMESTAMPTZ | | Last sync timestamp |
| sync_source | VARCHAR(30) | | CYGNET_BATCH, CYGNET_LIVE |
| cache_hit_count | INTEGER | DEFAULT 0 | Number of cache hits |
| gstr2b_alert | TEXT | | Alert message if issues |
| itc_note | TEXT | | ITC-related notes |

### Schema: `ebs`

#### ebs_events

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Internal identifier |
| event_code | VARCHAR(20) | UNIQUE, NOT NULL | Business ID (e.g., EBS001) |
| event_type | VARCHAR(30) | NOT NULL | PO_COMMITMENT, INVOICE_POST, GL_JOURNAL, FA_ADDITION |
| entity_id | VARCHAR(30) | | Source entity ID (PO/invoice) |
| entity_ref | VARCHAR(50) | | Source entity reference |
| description | TEXT | | Event description |
| gl_account | VARCHAR(20) | | Target GL account |
| amount | BIGINT | | Event amount (paise) |
| ebs_module | VARCHAR(10) | NOT NULL | Target EBS module: AP, GL, FA |
| status | VARCHAR(20) | NOT NULL | PENDING, ACKNOWLEDGED, FAILED |
| sent_at | TIMESTAMPTZ | | When sent to EBS |
| acknowledged_at | TIMESTAMPTZ | | When EBS acknowledged |
| ebs_ref | VARCHAR(50) | | EBS reference number |
| error_message | TEXT | | Error message if failed |

### Schema: `ai`

#### ai_insights

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Internal identifier |
| insight_code | VARCHAR(20) | UNIQUE, NOT NULL | Business ID (e.g., AI001) |
| agent | VARCHAR(50) | NOT NULL | Agent name |
| invoice_id | VARCHAR(20) | | Related invoice code |
| supplier_id | VARCHAR(20) | | Related supplier code |
| type | VARCHAR(30) | NOT NULL | GL_CODING, FRAUD_ALERT, MSME_SLA_RISK, MSME_SLA_BREACH, EARLY_PAYMENT, SUPPLIER_RISK |
| confidence | DECIMAL(5,1) | NOT NULL | Confidence score (0-100) |
| recommendation | TEXT | NOT NULL | Recommended action |
| reasoning | TEXT | | AI reasoning trace |
| applied | BOOLEAN | DEFAULT FALSE | Whether insight was applied |
| applied_at | TIMESTAMPTZ | | When applied |
| status | VARCHAR(20) | NOT NULL | PENDING_ACTION, RECOMMENDED, APPLIED, ESCALATED |

### Schema: `audit`

#### audit_logs

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Internal identifier |
| event_type | VARCHAR(100) | NOT NULL | Event type (e.g., invoice.approved) |
| entity_type | VARCHAR(50) | NOT NULL | Entity type (invoice, pr, po, etc.) |
| entity_id | VARCHAR(50) | | Entity identifier |
| actor | VARCHAR(255) | | Who performed the action |
| payload | JSONB | | Full event payload |
| timestamp | TIMESTAMPTZ | NOT NULL | Event timestamp |
| retention_until | TIMESTAMPTZ | | 7-year retention date (RBI) |

### Schema: `notifications`

#### notifications

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Internal identifier |
| type | VARCHAR(30) | NOT NULL | ALERT, INFO, WARNING, CRITICAL |
| recipient | VARCHAR(255) | NOT NULL | Target user or role |
| title | VARCHAR(255) | NOT NULL | Notification title |
| message | TEXT | NOT NULL | Notification body |
| link | VARCHAR(500) | | Deep link to relevant page |
| read | BOOLEAN | DEFAULT FALSE | Read status |
| created_at | TIMESTAMPTZ | NOT NULL | Creation time |

### Schema: `workflow`

#### approval_matrices

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Internal identifier |
| entity_type | VARCHAR(30) | NOT NULL | PR, PO, INVOICE |
| department | VARCHAR(10) | | Department code |
| min_amount | BIGINT | | Minimum amount threshold (paise) |
| max_amount | BIGINT | | Maximum amount threshold (paise) |
| approver_role | VARCHAR(50) | NOT NULL | Required approver role |
| auto_approve | BOOLEAN | DEFAULT FALSE | Auto-approve if AI confidence above threshold |
| confidence_threshold | DECIMAL(5,1) | | AI confidence threshold for auto-approval |

### Schema: `vendor_portal`

#### vendor_portal_events

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Internal identifier |
| event_code | VARCHAR(20) | UNIQUE, NOT NULL | Business ID (e.g., VPE001) |
| event_type | VARCHAR(50) | NOT NULL | vendor.onboarded, vendor.bank_verified, vendor.gstin_updated, vendor.document_expired |
| timestamp | TIMESTAMPTZ | NOT NULL | Event timestamp from portal |
| supplier_id | VARCHAR(20) | | Supplier code |
| supplier_name | VARCHAR(500) | | Supplier name |
| payload | JSONB | | Full event payload |
| processed | BOOLEAN | DEFAULT FALSE | Whether P2P has processed this event |
| p2p_action | TEXT | | Action taken by P2P platform |

## Entity Relationships

```
suppliers ----< purchase_requests (via supplier_preference)
suppliers ----< invoices (via supplier_id)
suppliers ----< gst_records (via gstin)

purchase_requests ----< pr_line_items
purchase_requests ----> purchase_orders (via po_id, 1:1)

purchase_orders ----< po_line_items
purchase_orders ----> goods_receipt_notes (via grn_id, 1:1)

goods_receipt_notes ----< grn_line_items

invoices ----> purchase_orders (via po_id, optional)
invoices ----> goods_receipt_notes (via grn_id, optional)
invoices ----< ai_insights (via invoice_id)
invoices ----< ebs_events (via entity_id)

suppliers ----< vendor_portal_events (via supplier_id)
suppliers ----< ai_insights (via supplier_id)
```

Key: `---->` = belongs to (FK), `----<` = has many
