"""
MSME Compliance Module — SQLAlchemy Models

No separate database table is needed for MSME compliance tracking.

All MSME-related data is stored directly on the Invoice model:
  - is_msme_supplier (Boolean)
  - msme_category (MICRO / SMALL / MEDIUM)
  - msme_days_remaining (Integer)
  - msme_due_date (date string)
  - msme_status (ON_TRACK / AT_RISK / BREACHED)
  - msme_penalty_amount (Float)

The MSME compliance service queries the invoices table to compute:
  - Section 43B(h) 45-day payment SLA status
  - At-risk and breached invoice counts
  - Penalty calculations (3x RBI rate compound interest)
  - SAMADHAAN integration status

See: backend/modules/invoices/models.py -> Invoice model
"""
