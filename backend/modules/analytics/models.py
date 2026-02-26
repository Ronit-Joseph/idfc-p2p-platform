"""
Analytics Module — SQLAlchemy Models

No separate database table is needed for the analytics module.

The spend analytics service aggregates data by querying other modules' tables:
  - invoices (spend by category, monthly trends, MTD spend)
  - purchase_orders (PO coverage, commitment tracking)
  - suppliers (top vendors, on-time payment rates)
  - budgets (budget vs actual, utilization percentages)

Analytics endpoints compute KPIs on-the-fly:
  - Invoice cycle time
  - 3-way match rate
  - Auto-approval rate
  - Early payment savings
  - Maverick spend percentage
  - PO coverage percentage

For production, consider materialised views or a dedicated analytics
data warehouse (e.g. Redshift / BigQuery) fed via Kafka CDC events.

See: backend/modules/analytics/service.py (to be implemented)
"""
