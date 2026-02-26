"""Database seeder -- populates all tables with prototype synthetic data.

Run from the p2p/ directory:
    python -m backend.seed           # seed if empty
    python -m backend.seed --force   # drop all tables and re-seed
"""

import asyncio
import json
import uuid
import sys
from datetime import datetime, timedelta

from passlib.context import CryptContext
from sqlalchemy import text

from backend.database import engine, async_session
from backend.base_model import Base

# ---------------------------------------------------------------------------
# Import ALL models so they register with Base.metadata
# ---------------------------------------------------------------------------
from backend.modules.auth.models import User
from backend.modules.suppliers.models import Supplier
from backend.modules.budgets.models import Budget, BudgetEncumbrance
from backend.modules.purchase_requests.models import PurchaseRequest, PRLineItem
from backend.modules.purchase_orders.models import (
    PurchaseOrder,
    POLineItem,
    GoodsReceiptNote,
    GRNLineItem,
)
from backend.modules.invoices.models import Invoice
from backend.modules.gst_cache.models import GSTRecord, GSTSyncLog
from backend.modules.ebs_integration.models import EBSEvent
from backend.modules.ai_agents.models import AIInsight, AgentConfig
from backend.modules.vendor_portal.models import VendorPortalEvent

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _id() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


def ts(days_ago: int = 0, hours_ago: int = 0) -> str:
    """ISO timestamp in the past."""
    d = datetime.now() - timedelta(days=days_ago, hours=hours_ago)
    return d.strftime("%Y-%m-%dT%H:%M:%S")


def ts_dt(days_ago: int = 0, hours_ago: int = 0) -> datetime:
    """datetime object in the past (for DateTime columns)."""
    return datetime.now() - timedelta(days=days_ago, hours=hours_ago)


def future(days: int = 0) -> str:
    """Date string in the future."""
    d = datetime.now() + timedelta(days=days)
    return d.strftime("%Y-%m-%d")


def past(days: int = 0) -> str:
    """Date string in the past."""
    d = datetime.now() - timedelta(days=days)
    return d.strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Fixed IDs -- we need stable references across entities
# ---------------------------------------------------------------------------

# Supplier IDs
SUP_IDS = {f"SUP{str(i).zfill(3)}": _id() for i in range(1, 16)}

# Budget IDs
BUD_IDS = {code: _id() for code in ["TECH", "OPS", "FIN", "MKT", "HR", "ADMIN"]}

# Purchase Request IDs
PR_IDS = {f"PR2024-{str(i).zfill(3)}": _id() for i in range(1, 9)}

# Purchase Order IDs
PO_IDS = {f"PO2024-{str(i).zfill(3)}": _id() for i in range(1, 4)}

# GRN IDs
GRN_IDS = {f"GRN2024-{str(i).zfill(3)}": _id() for i in range(1, 4)}

# Invoice IDs
INV_IDS = {f"INV{str(i).zfill(3)}": _id() for i in range(1, 8)}

# User IDs
USER_IDS = {
    "admin": _id(),
    "priya": _id(),
    "amit": _id(),
    "sunita": _id(),
    "rohan": _id(),
}

# EBS Event IDs
EBS_IDS = {f"EBS{str(i).zfill(3)}": _id() for i in range(1, 9)}

# AI Insight IDs
AI_IDS = {f"AI{str(i).zfill(3)}": _id() for i in range(1, 8)}

# Vendor Portal Event IDs
VPE_IDS = {f"VPE{str(i).zfill(3)}": _id() for i in range(1, 7)}


# ===================================================================
# DATA BUILDERS
# ===================================================================

def build_users() -> list[User]:
    """5 users: 1 admin + 4 department users."""
    return [
        User(
            id=USER_IDS["admin"],
            email="admin@idfc.com",
            hashed_password=pwd_context.hash("admin123"),
            full_name="System Admin",
            role="ADMIN",
            department=None,
            is_active=True,
        ),
        User(
            id=USER_IDS["priya"],
            email="priya.menon@idfc.com",
            hashed_password=pwd_context.hash("password"),
            full_name="Priya Menon",
            role="FINANCE_HEAD",
            department="FIN",
            is_active=True,
        ),
        User(
            id=USER_IDS["amit"],
            email="amit.sharma@idfc.com",
            hashed_password=pwd_context.hash("password"),
            full_name="Amit Sharma",
            role="DEPARTMENT_HEAD",
            department="TECH",
            is_active=True,
        ),
        User(
            id=USER_IDS["sunita"],
            email="sunita.rao@idfc.com",
            hashed_password=pwd_context.hash("password"),
            full_name="Sunita Rao",
            role="PROCUREMENT_MANAGER",
            department="ADMIN",
            is_active=True,
        ),
        User(
            id=USER_IDS["rohan"],
            email="rohan.joshi@idfc.com",
            hashed_password=pwd_context.hash("password"),
            full_name="Rohan Joshi",
            role="DEPARTMENT_HEAD",
            department="OPS",
            is_active=True,
        ),
    ]


def build_suppliers() -> list[Supplier]:
    """15 supplier records."""
    return [
        Supplier(
            id=SUP_IDS["SUP001"],
            code="SUP001",
            legal_name="TechMahindra Solutions Pvt Ltd",
            gstin="27AATCM5678P1ZS",
            pan="AATCM5678P",
            state="Maharashtra",
            category="IT Services",
            is_msme=False,
            msme_category=None,
            bank_account="9876543210001",
            bank_name="HDFC Bank",
            ifsc="HDFC0001234",
            payment_terms=30,
            risk_score=2.1,
            status="ACTIVE",
            vendor_portal_status="VERIFIED",
            contact_email="accounts@techmahindra.com",
            onboarded_date=past(365),
        ),
        Supplier(
            id=SUP_IDS["SUP002"],
            code="SUP002",
            legal_name="Wipro Infrastructure Ltd",
            gstin="29AATCW1234K1ZT",
            pan="AATCW1234K",
            state="Karnataka",
            category="Facilities Management",
            is_msme=False,
            msme_category=None,
            bank_account="9876543210002",
            bank_name="ICICI Bank",
            ifsc="ICIC0002345",
            payment_terms=45,
            risk_score=1.8,
            status="ACTIVE",
            vendor_portal_status="VERIFIED",
            contact_email="finance@wipro-infra.com",
            onboarded_date=past(400),
        ),
        Supplier(
            id=SUP_IDS["SUP003"],
            code="SUP003",
            legal_name="Rajesh Office Suppliers",
            gstin="27AABCR4321A1ZK",
            pan="AABCR4321A",
            state="Maharashtra",
            category="Office Supplies",
            is_msme=True,
            msme_category="MICRO",
            bank_account="9876543210003",
            bank_name="Bank of Baroda",
            ifsc="BARB0003456",
            payment_terms=15,
            risk_score=3.4,
            status="ACTIVE",
            vendor_portal_status="VERIFIED",
            contact_email="rajesh@rajeshoffice.in",
            onboarded_date=past(180),
        ),
        Supplier(
            id=SUP_IDS["SUP004"],
            code="SUP004",
            legal_name="ITC Business Solutions",
            gstin="07AABCI5678B1ZP",
            pan="AABCI5678B",
            state="Delhi",
            category="Professional Services",
            is_msme=False,
            msme_category=None,
            bank_account="9876543210004",
            bank_name="Axis Bank",
            ifsc="UTIB0004567",
            payment_terms=30,
            risk_score=1.5,
            status="ACTIVE",
            vendor_portal_status="VERIFIED",
            contact_email="billing@itcbusiness.com",
            onboarded_date=past(500),
        ),
        Supplier(
            id=SUP_IDS["SUP005"],
            code="SUP005",
            legal_name="Gujarat Tech Solutions",
            gstin="24AATCG9876C1ZM",
            pan="AATCG9876C",
            state="Gujarat",
            category="IT Services",
            is_msme=True,
            msme_category="SMALL",
            bank_account="9876543210005",
            bank_name="State Bank of India",
            ifsc="SBIN0005678",
            payment_terms=30,
            risk_score=2.8,
            status="ACTIVE",
            vendor_portal_status="VERIFIED",
            contact_email="info@gujarattech.co.in",
            onboarded_date=past(220),
        ),
        Supplier(
            id=SUP_IDS["SUP006"],
            code="SUP006",
            legal_name="Sodexo Facilities India Pvt Ltd",
            gstin="29AATCS2345D1ZN",
            pan="AATCS2345D",
            state="Karnataka",
            category="Facilities Management",
            is_msme=False,
            msme_category=None,
            bank_account="9876543210006",
            bank_name="Citibank",
            ifsc="CITI0006789",
            payment_terms=45,
            risk_score=1.2,
            status="ACTIVE",
            vendor_portal_status="VERIFIED",
            contact_email="accounts@sodexo.in",
            onboarded_date=past(600),
        ),
        Supplier(
            id=SUP_IDS["SUP007"],
            code="SUP007",
            legal_name="Mumbai Print House",
            gstin="27AABCM7654E1ZQ",
            pan="AABCM7654E",
            state="Maharashtra",
            category="Printing & Marketing",
            is_msme=True,
            msme_category="MICRO",
            bank_account="9876543210007",
            bank_name="Union Bank of India",
            ifsc="UBIN0007890",
            payment_terms=15,
            risk_score=4.1,
            status="ACTIVE",
            vendor_portal_status="VERIFIED",
            contact_email="orders@mumbaiprinthouse.in",
            onboarded_date=past(150),
        ),
        Supplier(
            id=SUP_IDS["SUP008"],
            code="SUP008",
            legal_name="Deloitte Advisory LLP",
            gstin="07AATCD3456F1ZR",
            pan="AATCD3456F",
            state="Delhi",
            category="Consulting",
            is_msme=False,
            msme_category=None,
            bank_account="9876543210008",
            bank_name="Deutsche Bank",
            ifsc="DEUT0008901",
            payment_terms=60,
            risk_score=1.1,
            status="ACTIVE",
            vendor_portal_status="VERIFIED",
            contact_email="invoices@deloitte.com",
            onboarded_date=past(730),
        ),
        Supplier(
            id=SUP_IDS["SUP009"],
            code="SUP009",
            legal_name="Suresh Traders Pvt Ltd",
            gstin="27AABCS8765H1ZT",
            pan="AABCS8765H",
            state="Maharashtra",
            category="Office Supplies",
            is_msme=True,
            msme_category="MICRO",
            bank_account="9876543210009",
            bank_name="Punjab National Bank",
            ifsc="PUNB0009012",
            payment_terms=15,
            risk_score=3.8,
            status="ACTIVE",
            vendor_portal_status="VERIFIED",
            contact_email="suresh@sureshtraders.in",
            onboarded_date=past(200),
        ),
        Supplier(
            id=SUP_IDS["SUP010"],
            code="SUP010",
            legal_name="Infosys BPM Ltd",
            gstin="29AATCI3456J1ZV",
            pan="AATCI3456J",
            state="Karnataka",
            category="IT Services",
            is_msme=False,
            msme_category=None,
            bank_account="9876543210010",
            bank_name="HDFC Bank",
            ifsc="HDFC0010123",
            payment_terms=30,
            risk_score=1.3,
            status="ACTIVE",
            vendor_portal_status="VERIFIED",
            contact_email="ap@infosysbpm.com",
            onboarded_date=past(450),
        ),
        Supplier(
            id=SUP_IDS["SUP011"],
            code="SUP011",
            legal_name="Karnataka Tech MSME Solutions",
            gstin="29AABCK5432K1ZW",
            pan="AABCK5432K",
            state="Karnataka",
            category="IT Services",
            is_msme=True,
            msme_category="SMALL",
            bank_account="9876543210011",
            bank_name="Canara Bank",
            ifsc="CNRB0011234",
            payment_terms=30,
            risk_score=3.2,
            status="ACTIVE",
            vendor_portal_status="VERIFIED",
            contact_email="hello@ktmsolutions.in",
            onboarded_date=past(130),
        ),
        Supplier(
            id=SUP_IDS["SUP012"],
            code="SUP012",
            legal_name="Delhi Stationery Hub",
            gstin="07AABCD6789M1ZY",
            pan="AABCD6789M",
            state="Delhi",
            category="Office Supplies",
            is_msme=True,
            msme_category="MICRO",
            bank_account="9876543210012",
            bank_name="Indian Bank",
            ifsc="IDIB0012345",
            payment_terms=15,
            risk_score=4.5,
            status="ACTIVE",
            vendor_portal_status="PENDING_VERIFICATION",
            contact_email="sales@delhistationery.com",
            onboarded_date=past(45),
        ),
        Supplier(
            id=SUP_IDS["SUP013"],
            code="SUP013",
            legal_name="HCL Technologies Ltd",
            gstin="09AATCH6543G1ZS",
            pan="AATCH6543G",
            state="Uttar Pradesh",
            category="IT Services",
            is_msme=False,
            msme_category=None,
            bank_account="9876543210013",
            bank_name="ICICI Bank",
            ifsc="ICIC0013456",
            payment_terms=30,
            risk_score=1.6,
            status="ACTIVE",
            vendor_portal_status="VERIFIED",
            contact_email="payments@hcl.com",
            onboarded_date=past(550),
        ),
        Supplier(
            id=SUP_IDS["SUP014"],
            code="SUP014",
            legal_name="KPMG India Pvt Ltd",
            gstin="07AATCK4567I1ZU",
            pan="AATCK4567I",
            state="Delhi",
            category="Consulting",
            is_msme=False,
            msme_category=None,
            bank_account="9876543210014",
            bank_name="Standard Chartered",
            ifsc="SCBL0014567",
            payment_terms=60,
            risk_score=1.0,
            status="ACTIVE",
            vendor_portal_status="VERIFIED",
            contact_email="billing@kpmg.com",
            onboarded_date=past(800),
        ),
        Supplier(
            id=SUP_IDS["SUP015"],
            code="SUP015",
            legal_name="Compass India Services Pvt Ltd",
            gstin="07AATCM2345L1ZX",
            pan="AATCM2345L",
            state="Delhi",
            category="Facilities Management",
            is_msme=False,
            msme_category=None,
            bank_account="9876543210015",
            bank_name="Kotak Mahindra Bank",
            ifsc="KKBK0015678",
            payment_terms=30,
            risk_score=1.7,
            status="ACTIVE",
            vendor_portal_status="VERIFIED",
            contact_email="vendor@compassindia.com",
            onboarded_date=past(320),
        ),
    ]


def build_budgets() -> list[Budget]:
    """6 department budgets for FY2024-25."""
    return [
        Budget(
            id=BUD_IDS["TECH"],
            department_code="TECH",
            department_name="Technology",
            gl_account="6100",
            cost_center="CC-TECH-01",
            fiscal_year="FY2024-25",
            total_amount=80000000,
            committed_amount=22000000,
            actual_amount=30000000,
            available_amount=28000000,
            currency="INR",
        ),
        Budget(
            id=BUD_IDS["OPS"],
            department_code="OPS",
            department_name="Operations",
            gl_account="6200",
            cost_center="CC-OPS-01",
            fiscal_year="FY2024-25",
            total_amount=40000000,
            committed_amount=8000000,
            actual_amount=12000000,
            available_amount=20000000,
            currency="INR",
        ),
        Budget(
            id=BUD_IDS["FIN"],
            department_code="FIN",
            department_name="Finance",
            gl_account="6300",
            cost_center="CC-FIN-01",
            fiscal_year="FY2024-25",
            total_amount=30000000,
            committed_amount=5000000,
            actual_amount=10500000,
            available_amount=14500000,
            currency="INR",
        ),
        Budget(
            id=BUD_IDS["MKT"],
            department_code="MKT",
            department_name="Marketing",
            gl_account="6400",
            cost_center="CC-MKT-01",
            fiscal_year="FY2024-25",
            total_amount=20000000,
            committed_amount=4000000,
            actual_amount=8000000,
            available_amount=8000000,
            currency="INR",
        ),
        Budget(
            id=BUD_IDS["HR"],
            department_code="HR",
            department_name="Human Resources",
            gl_account="6500",
            cost_center="CC-HR-01",
            fiscal_year="FY2024-25",
            total_amount=10000000,
            committed_amount=1500000,
            actual_amount=2500000,
            available_amount=6000000,
            currency="INR",
        ),
        Budget(
            id=BUD_IDS["ADMIN"],
            department_code="ADMIN",
            department_name="Administration",
            gl_account="6600",
            cost_center="CC-ADMIN-01",
            fiscal_year="FY2024-25",
            total_amount=15000000,
            committed_amount=3000000,
            actual_amount=8000000,
            available_amount=4000000,
            currency="INR",
        ),
    ]


def build_purchase_requests() -> tuple[list[PurchaseRequest], list[PRLineItem]]:
    """8 purchase requests + their line items."""
    prs = [
        PurchaseRequest(
            id=PR_IDS["PR2024-001"],
            pr_number="PR2024-001",
            title="Annual IT Infrastructure Upgrade - Servers & Networking",
            department="TECH",
            requester="Amit Sharma",
            requester_email="amit.sharma@idfc.com",
            amount=12500000,
            currency="INR",
            gl_account="6100",
            cost_center="CC-TECH-01",
            category="IT Services",
            supplier_preference="SUP001",
            justification="Annual refresh of core banking servers. Current servers are 4 years old with increasing failure rates. Required for RBI compliance on system uptime SLA.",
            status="PO_CREATED",
            po_id=PO_IDS["PO2024-001"],
            budget_check="APPROVED",
            budget_available_at_time=28000000,
            approved_at=ts_dt(days_ago=25),
            approver="Priya Menon",
            rejection_reason=None,
            rejected_at=None,
        ),
        PurchaseRequest(
            id=PR_IDS["PR2024-002"],
            pr_number="PR2024-002",
            title="Office Supplies Q3 - Stationery & Consumables",
            department="ADMIN",
            requester="Sunita Rao",
            requester_email="sunita.rao@idfc.com",
            amount=285000,
            currency="INR",
            gl_account="6600",
            cost_center="CC-ADMIN-01",
            category="Office Supplies",
            supplier_preference="SUP003",
            justification="Quarterly stationery replenishment for all branches. MSME vendor - priority processing required under Section 43B(h).",
            status="PO_CREATED",
            po_id=PO_IDS["PO2024-002"],
            budget_check="APPROVED",
            budget_available_at_time=4000000,
            approved_at=ts_dt(days_ago=20),
            approver="Priya Menon",
            rejection_reason=None,
            rejected_at=None,
        ),
        PurchaseRequest(
            id=PR_IDS["PR2024-003"],
            pr_number="PR2024-003",
            title="Facility Management Contract - Annual Renewal",
            department="OPS",
            requester="Rohan Joshi",
            requester_email="rohan.joshi@idfc.com",
            amount=8500000,
            currency="INR",
            gl_account="6200",
            cost_center="CC-OPS-01",
            category="Facilities Management",
            supplier_preference="SUP006",
            justification="Annual renewal of facility management contract covering 12 branch offices in Karnataka region. Sodexo has been providing excellent service with 99.2% SLA compliance.",
            status="PO_CREATED",
            po_id=PO_IDS["PO2024-003"],
            budget_check="APPROVED",
            budget_available_at_time=20000000,
            approved_at=ts_dt(days_ago=18),
            approver="Priya Menon",
            rejection_reason=None,
            rejected_at=None,
        ),
        PurchaseRequest(
            id=PR_IDS["PR2024-004"],
            pr_number="PR2024-004",
            title="Cybersecurity Assessment & Penetration Testing",
            department="TECH",
            requester="Amit Sharma",
            requester_email="amit.sharma@idfc.com",
            amount=4200000,
            currency="INR",
            gl_account="6100",
            cost_center="CC-TECH-01",
            category="Professional Services",
            supplier_preference="SUP008",
            justification="Annual cybersecurity audit mandated by RBI circular on IT governance. Deloitte was selected via competitive bidding. Covers VAPT, SOC review, and DR testing.",
            status="APPROVED",
            po_id=None,
            budget_check="APPROVED",
            budget_available_at_time=28000000,
            approved_at=ts_dt(days_ago=10),
            approver="Priya Menon",
            rejection_reason=None,
            rejected_at=None,
        ),
        PurchaseRequest(
            id=PR_IDS["PR2024-005"],
            pr_number="PR2024-005",
            title="Marketing Collateral - Annual Report Printing",
            department="MKT",
            requester="Vikram Patel",
            requester_email="vikram.patel@idfc.com",
            amount=750000,
            currency="INR",
            gl_account="6400",
            cost_center="CC-MKT-01",
            category="Printing & Marketing",
            supplier_preference="SUP007",
            justification="Printing 5000 copies of annual report and 10000 marketing brochures. MSME vendor with competitive rates.",
            status="PENDING_APPROVAL",
            po_id=None,
            budget_check="APPROVED",
            budget_available_at_time=8000000,
            approved_at=None,
            approver=None,
            rejection_reason=None,
            rejected_at=None,
        ),
        PurchaseRequest(
            id=PR_IDS["PR2024-006"],
            pr_number="PR2024-006",
            title="Cloud Infrastructure - AWS Reserved Instances",
            department="TECH",
            requester="Amit Sharma",
            requester_email="amit.sharma@idfc.com",
            amount=18000000,
            currency="INR",
            gl_account="6100",
            cost_center="CC-TECH-01",
            category="IT Services",
            supplier_preference="SUP010",
            justification="3-year reserved instance commitment for core banking workloads on AWS. Expected 40% savings vs on-demand pricing. Infosys BPM as managed services partner.",
            status="PENDING_APPROVAL",
            po_id=None,
            budget_check="APPROVED",
            budget_available_at_time=28000000,
            approved_at=None,
            approver=None,
            rejection_reason=None,
            rejected_at=None,
        ),
        PurchaseRequest(
            id=PR_IDS["PR2024-007"],
            pr_number="PR2024-007",
            title="Employee Wellness Program - Annual Contract",
            department="HR",
            requester="Meera Reddy",
            requester_email="meera.reddy@idfc.com",
            amount=3200000,
            currency="INR",
            gl_account="6500",
            cost_center="CC-HR-01",
            category="Professional Services",
            supplier_preference="SUP004",
            justification="Comprehensive employee wellness program including health camps, mental health counseling, and ergonomic assessments across all offices.",
            status="REJECTED",
            po_id=None,
            budget_check="APPROVED",
            budget_available_at_time=6000000,
            approved_at=None,
            approver=None,
            rejection_reason="Budget constraints - please resubmit in Q4 with reduced scope. HR budget is prioritized for recruitment drives this quarter.",
            rejected_at=ts_dt(days_ago=5),
        ),
        PurchaseRequest(
            id=PR_IDS["PR2024-008"],
            pr_number="PR2024-008",
            title="Office Furniture Replacement - Mumbai HQ",
            department="ADMIN",
            requester="Sunita Rao",
            requester_email="sunita.rao@idfc.com",
            amount=1800000,
            currency="INR",
            gl_account="6600",
            cost_center="CC-ADMIN-01",
            category="Office Supplies",
            supplier_preference="SUP009",
            justification="Replacement of 150 workstations in Mumbai HQ. Current furniture is 7 years old and multiple ergonomic complaints have been filed. MSME supplier with competitive quote.",
            status="DRAFT",
            po_id=None,
            budget_check=None,
            budget_available_at_time=None,
            approved_at=None,
            approver=None,
            rejection_reason=None,
            rejected_at=None,
        ),
    ]

    # PR Line Items
    line_items = [
        # PR2024-001 items
        PRLineItem(id=_id(), pr_id=PR_IDS["PR2024-001"], description="Dell PowerEdge R750 Rack Server", quantity=10, unit="PCS", unit_price=850000, sort_order=1),
        PRLineItem(id=_id(), pr_id=PR_IDS["PR2024-001"], description="Cisco Catalyst 9300 Switch", quantity=5, unit="PCS", unit_price=320000, sort_order=2),
        PRLineItem(id=_id(), pr_id=PR_IDS["PR2024-001"], description="Server Installation & Configuration", quantity=1, unit="LS", unit_price=900000, sort_order=3),
        # PR2024-002 items
        PRLineItem(id=_id(), pr_id=PR_IDS["PR2024-002"], description="A4 Copier Paper (500 sheets)", quantity=500, unit="REAM", unit_price=250, sort_order=1),
        PRLineItem(id=_id(), pr_id=PR_IDS["PR2024-002"], description="Printer Toner Cartridge HP 26A", quantity=50, unit="PCS", unit_price=2800, sort_order=2),
        PRLineItem(id=_id(), pr_id=PR_IDS["PR2024-002"], description="Assorted Stationery Kit", quantity=100, unit="BOX", unit_price=450, sort_order=3),
        # PR2024-003 items
        PRLineItem(id=_id(), pr_id=PR_IDS["PR2024-003"], description="Facility Management - 12 Branches (Annual)", quantity=12, unit="YEAR", unit_price=600000, sort_order=1),
        PRLineItem(id=_id(), pr_id=PR_IDS["PR2024-003"], description="Deep Cleaning Services (Quarterly)", quantity=4, unit="QUARTER", unit_price=125000, sort_order=2),
        # PR2024-004 items
        PRLineItem(id=_id(), pr_id=PR_IDS["PR2024-004"], description="VAPT Assessment (External & Internal)", quantity=1, unit="LS", unit_price=1800000, sort_order=1),
        PRLineItem(id=_id(), pr_id=PR_IDS["PR2024-004"], description="SOC 2 Type II Audit", quantity=1, unit="LS", unit_price=1500000, sort_order=2),
        PRLineItem(id=_id(), pr_id=PR_IDS["PR2024-004"], description="DR Testing & Report", quantity=1, unit="LS", unit_price=900000, sort_order=3),
        # PR2024-005 items
        PRLineItem(id=_id(), pr_id=PR_IDS["PR2024-005"], description="Annual Report Printing (200pg, Hardbound)", quantity=5000, unit="PCS", unit_price=95, sort_order=1),
        PRLineItem(id=_id(), pr_id=PR_IDS["PR2024-005"], description="Marketing Brochure (16pg, Glossy)", quantity=10000, unit="PCS", unit_price=28, sort_order=2),
        # PR2024-006 items
        PRLineItem(id=_id(), pr_id=PR_IDS["PR2024-006"], description="AWS EC2 Reserved Instances (3yr)", quantity=1, unit="LS", unit_price=12000000, sort_order=1),
        PRLineItem(id=_id(), pr_id=PR_IDS["PR2024-006"], description="Managed Services - Infosys BPM (Annual)", quantity=1, unit="YEAR", unit_price=6000000, sort_order=2),
        # PR2024-007 items
        PRLineItem(id=_id(), pr_id=PR_IDS["PR2024-007"], description="Employee Health Camps (Monthly)", quantity=12, unit="MONTH", unit_price=120000, sort_order=1),
        PRLineItem(id=_id(), pr_id=PR_IDS["PR2024-007"], description="Mental Health Counseling Services", quantity=1, unit="YEAR", unit_price=1200000, sort_order=2),
        PRLineItem(id=_id(), pr_id=PR_IDS["PR2024-007"], description="Ergonomic Assessment (All Offices)", quantity=1, unit="LS", unit_price=560000, sort_order=3),
        # PR2024-008 items
        PRLineItem(id=_id(), pr_id=PR_IDS["PR2024-008"], description="Ergonomic Workstation Desk", quantity=150, unit="PCS", unit_price=8500, sort_order=1),
        PRLineItem(id=_id(), pr_id=PR_IDS["PR2024-008"], description="Ergonomic Office Chair", quantity=150, unit="PCS", unit_price=3500, sort_order=2),
    ]

    return prs, line_items


def build_purchase_orders() -> tuple[list[PurchaseOrder], list[POLineItem]]:
    """3 purchase orders + their line items."""
    pos = [
        PurchaseOrder(
            id=PO_IDS["PO2024-001"],
            po_number="PO2024-001",
            pr_id=PR_IDS["PR2024-001"],
            supplier_id=SUP_IDS["SUP001"],
            amount=12500000,
            currency="INR",
            status="RECEIVED",
            delivery_date=past(5),
            dispatch_date=ts_dt(days_ago=10),
            acknowledged_date=ts_dt(days_ago=23),
            ebs_commitment_status="POSTED",
            ebs_commitment_ref="EBS-PO-45231",
        ),
        PurchaseOrder(
            id=PO_IDS["PO2024-002"],
            po_number="PO2024-002",
            pr_id=PR_IDS["PR2024-002"],
            supplier_id=SUP_IDS["SUP003"],
            amount=285000,
            currency="INR",
            status="RECEIVED",
            delivery_date=past(3),
            dispatch_date=ts_dt(days_ago=8),
            acknowledged_date=ts_dt(days_ago=18),
            ebs_commitment_status="POSTED",
            ebs_commitment_ref="EBS-PO-45232",
        ),
        PurchaseOrder(
            id=PO_IDS["PO2024-003"],
            po_number="PO2024-003",
            pr_id=PR_IDS["PR2024-003"],
            supplier_id=SUP_IDS["SUP006"],
            amount=8500000,
            currency="INR",
            status="ACKNOWLEDGED",
            delivery_date=future(30),
            dispatch_date=None,
            acknowledged_date=ts_dt(days_ago=15),
            ebs_commitment_status="POSTED",
            ebs_commitment_ref="EBS-PO-45233",
        ),
    ]

    line_items = [
        # PO2024-001 items
        POLineItem(id=_id(), po_id=PO_IDS["PO2024-001"], description="Dell PowerEdge R750 Rack Server", quantity=10, unit="PCS", unit_price=850000, total=8500000, grn_quantity=10, sort_order=1),
        POLineItem(id=_id(), po_id=PO_IDS["PO2024-001"], description="Cisco Catalyst 9300 Switch", quantity=5, unit="PCS", unit_price=320000, total=1600000, grn_quantity=5, sort_order=2),
        POLineItem(id=_id(), po_id=PO_IDS["PO2024-001"], description="Server Installation & Configuration", quantity=1, unit="LS", unit_price=900000, total=900000, grn_quantity=1, sort_order=3),
        # PO2024-002 items
        POLineItem(id=_id(), po_id=PO_IDS["PO2024-002"], description="A4 Copier Paper (500 sheets)", quantity=500, unit="REAM", unit_price=250, total=125000, grn_quantity=500, sort_order=1),
        POLineItem(id=_id(), po_id=PO_IDS["PO2024-002"], description="Printer Toner Cartridge HP 26A", quantity=50, unit="PCS", unit_price=2800, total=140000, grn_quantity=50, sort_order=2),
        POLineItem(id=_id(), po_id=PO_IDS["PO2024-002"], description="Assorted Stationery Kit", quantity=100, unit="BOX", unit_price=450, total=45000, grn_quantity=100, sort_order=3),
        # PO2024-003 items
        POLineItem(id=_id(), po_id=PO_IDS["PO2024-003"], description="Facility Management - 12 Branches (Annual)", quantity=12, unit="YEAR", unit_price=600000, total=7200000, grn_quantity=0, sort_order=1),
        POLineItem(id=_id(), po_id=PO_IDS["PO2024-003"], description="Deep Cleaning Services (Quarterly)", quantity=4, unit="QUARTER", unit_price=125000, total=500000, grn_quantity=0, sort_order=2),
    ]

    return pos, line_items


def build_grns() -> tuple[list[GoodsReceiptNote], list[GRNLineItem]]:
    """3 goods receipt notes + their line items."""
    grns = [
        GoodsReceiptNote(
            id=GRN_IDS["GRN2024-001"],
            grn_number="GRN2024-001",
            po_id=PO_IDS["PO2024-001"],
            received_date=past(5),
            received_by="Amit Sharma",
            status="COMPLETE",
            notes="All 10 servers and 5 switches received in good condition. Installation completed and verified.",
        ),
        GoodsReceiptNote(
            id=GRN_IDS["GRN2024-002"],
            grn_number="GRN2024-002",
            po_id=PO_IDS["PO2024-002"],
            received_date=past(3),
            received_by="Sunita Rao",
            status="COMPLETE",
            notes="All stationery items received as per PO. Quality check passed.",
        ),
        GoodsReceiptNote(
            id=GRN_IDS["GRN2024-003"],
            grn_number="GRN2024-003",
            po_id=PO_IDS["PO2024-003"],
            received_date=past(1),
            received_by="Rohan Joshi",
            status="PARTIAL",
            notes="Service commencement acknowledged for first quarter. Remaining quarters pending.",
        ),
    ]

    line_items = [
        # GRN2024-001 items
        GRNLineItem(id=_id(), grn_id=GRN_IDS["GRN2024-001"], description="Dell PowerEdge R750 Rack Server", po_quantity=10, received_quantity=10, unit="PCS"),
        GRNLineItem(id=_id(), grn_id=GRN_IDS["GRN2024-001"], description="Cisco Catalyst 9300 Switch", po_quantity=5, received_quantity=5, unit="PCS"),
        GRNLineItem(id=_id(), grn_id=GRN_IDS["GRN2024-001"], description="Server Installation & Configuration", po_quantity=1, received_quantity=1, unit="LS"),
        # GRN2024-002 items
        GRNLineItem(id=_id(), grn_id=GRN_IDS["GRN2024-002"], description="A4 Copier Paper (500 sheets)", po_quantity=500, received_quantity=500, unit="REAM"),
        GRNLineItem(id=_id(), grn_id=GRN_IDS["GRN2024-002"], description="Printer Toner Cartridge HP 26A", po_quantity=50, received_quantity=50, unit="PCS"),
        GRNLineItem(id=_id(), grn_id=GRN_IDS["GRN2024-002"], description="Assorted Stationery Kit", po_quantity=100, received_quantity=100, unit="BOX"),
        # GRN2024-003 items
        GRNLineItem(id=_id(), grn_id=GRN_IDS["GRN2024-003"], description="Facility Management - 12 Branches (Q1)", po_quantity=12, received_quantity=3, unit="YEAR"),
        GRNLineItem(id=_id(), grn_id=GRN_IDS["GRN2024-003"], description="Deep Cleaning Services (Q1)", po_quantity=4, received_quantity=1, unit="QUARTER"),
    ]

    return grns, line_items


def build_invoices() -> list[Invoice]:
    """7 invoices spanning different statuses and scenarios."""
    return [
        Invoice(
            id=INV_IDS["INV001"],
            invoice_number="INV001",
            supplier_id=SUP_IDS["SUP001"],
            po_id=PO_IDS["PO2024-001"],
            grn_id=GRN_IDS["GRN2024-001"],
            invoice_date=past(4),
            due_date=future(26),
            subtotal=12500000,
            gst_rate=18.0,
            gst_amount=2250000,
            tds_rate=2.0,
            tds_amount=250000,
            total_amount=14750000,
            net_payable=14500000,
            gstin_supplier="27AATCM5678P1ZS",
            gstin_buyer="27AABCI1234D1ZP",
            hsn_sac="998314",
            irn="INV001-IRN-2024-TM-78234",
            status="POSTED_TO_EBS",
            ocr_confidence=97.5,
            gstin_cache_status="VALID",
            gstin_validated_from_cache=True,
            gstr2b_itc_eligible=True,
            gstin_cache_age_hours=2.3,
            match_status="3WAY_MATCH_PASSED",
            match_variance=0.0,
            match_exception_reason=None,
            match_note="PO amount matches invoice. GRN confirms full delivery. 3-way match passed.",
            coding_agent_gl="6100",
            coding_agent_confidence=0.96,
            coding_agent_category="IT Services - Hardware & Infrastructure",
            fraud_flag=False,
            fraud_reasons=[],
            cash_opt_suggestion="Standard payment terms apply. No early payment discount available.",
            ebs_ap_status="POSTED",
            ebs_ap_ref="EBS-AP-78234",
            ebs_posted_at=ts_dt(days_ago=2),
            approved_by="Priya Menon",
            approved_at=ts_dt(days_ago=3),
            rejected_by=None,
            rejected_at=None,
            rejection_reason=None,
            is_msme_supplier=False,
            msme_category=None,
            msme_days_remaining=None,
            msme_due_date=None,
            msme_status=None,
            msme_penalty_amount=0,
            uploaded_by="Sunita Rao",
        ),
        Invoice(
            id=INV_IDS["INV002"],
            invoice_number="INV002",
            supplier_id=SUP_IDS["SUP003"],
            po_id=PO_IDS["PO2024-002"],
            grn_id=GRN_IDS["GRN2024-002"],
            invoice_date=past(3),
            due_date=future(12),
            subtotal=285000,
            gst_rate=18.0,
            gst_amount=51300,
            tds_rate=0.0,
            tds_amount=0,
            total_amount=336300,
            net_payable=336300,
            gstin_supplier="27AABCR4321A1ZK",
            gstin_buyer="27AABCI1234D1ZP",
            hsn_sac="4802",
            irn="INV002-IRN-2024-ROS-78235",
            status="APPROVED",
            ocr_confidence=94.2,
            gstin_cache_status="VALID",
            gstin_validated_from_cache=True,
            gstr2b_itc_eligible=True,
            gstin_cache_age_hours=1.1,
            match_status="3WAY_MATCH_PASSED",
            match_variance=0.0,
            match_exception_reason=None,
            match_note="PO amount matches invoice. GRN confirms full delivery. MSME supplier - priority processing.",
            coding_agent_gl="6600",
            coding_agent_confidence=0.92,
            coding_agent_category="Office Supplies - Stationery & Consumables",
            fraud_flag=False,
            fraud_reasons=[],
            cash_opt_suggestion="MSME supplier - must pay within 45 days per Section 43B(h). Recommend immediate processing.",
            ebs_ap_status="PENDING",
            ebs_ap_ref=None,
            ebs_posted_at=None,
            approved_by="Priya Menon",
            approved_at=ts_dt(days_ago=1),
            rejected_by=None,
            rejected_at=None,
            rejection_reason=None,
            is_msme_supplier=True,
            msme_category="MICRO",
            msme_days_remaining=38,
            msme_due_date=future(38),
            msme_status="ON_TRACK",
            msme_penalty_amount=0,
            uploaded_by="Sunita Rao",
        ),
        Invoice(
            id=INV_IDS["INV003"],
            invoice_number="INV003",
            supplier_id=SUP_IDS["SUP006"],
            po_id=PO_IDS["PO2024-003"],
            grn_id=GRN_IDS["GRN2024-003"],
            invoice_date=past(1),
            due_date=future(44),
            subtotal=2125000,
            gst_rate=18.0,
            gst_amount=382500,
            tds_rate=2.0,
            tds_amount=42500,
            total_amount=2507500,
            net_payable=2465000,
            gstin_supplier="29AATCS2345D1ZN",
            gstin_buyer="27AABCI1234D1ZP",
            hsn_sac="998512",
            irn=None,
            status="MATCHED",
            ocr_confidence=98.1,
            gstin_cache_status="VALID",
            gstin_validated_from_cache=True,
            gstr2b_itc_eligible=True,
            gstin_cache_age_hours=0.5,
            match_status="3WAY_MATCH_PASSED",
            match_variance=0.0,
            match_exception_reason=None,
            match_note="Partial delivery (Q1 of annual contract). Invoice for first quarter matches proportional PO amount.",
            coding_agent_gl="6200",
            coding_agent_confidence=0.94,
            coding_agent_category="Facilities Management - Annual Contract",
            fraud_flag=False,
            fraud_reasons=[],
            cash_opt_suggestion="Standard payment terms. Consider early payment for 1.5% discount if cash position allows.",
            ebs_ap_status="NOT_STARTED",
            ebs_ap_ref=None,
            ebs_posted_at=None,
            approved_by=None,
            approved_at=None,
            rejected_by=None,
            rejected_at=None,
            rejection_reason=None,
            is_msme_supplier=False,
            msme_category=None,
            msme_days_remaining=None,
            msme_due_date=None,
            msme_status=None,
            msme_penalty_amount=0,
            uploaded_by="Rohan Joshi",
        ),
        Invoice(
            id=INV_IDS["INV004"],
            invoice_number="INV004",
            supplier_id=SUP_IDS["SUP005"],
            po_id=None,
            grn_id=None,
            invoice_date=past(2),
            due_date=future(28),
            subtotal=950000,
            gst_rate=18.0,
            gst_amount=171000,
            tds_rate=10.0,
            tds_amount=95000,
            total_amount=1121000,
            net_payable=1026000,
            gstin_supplier="24AATCG9876C1ZM",
            gstin_buyer="27AABCI1234D1ZP",
            hsn_sac="998314",
            irn=None,
            status="EXCEPTION",
            ocr_confidence=85.3,
            gstin_cache_status="VALID",
            gstin_validated_from_cache=True,
            gstr2b_itc_eligible=True,
            gstin_cache_age_hours=5.2,
            match_status="3WAY_MATCH_EXCEPTION",
            match_variance=15.0,
            match_exception_reason="No matching PO found. Invoice submitted without purchase order reference.",
            match_note="Non-PO invoice from MSME supplier. Requires manual approval per policy. TDS rate appears high - verify applicable section.",
            coding_agent_gl="6100",
            coding_agent_confidence=0.78,
            coding_agent_category="IT Services - Software Development",
            fraud_flag=False,
            fraud_reasons=[],
            cash_opt_suggestion="MSME SMALL supplier. Section 43B(h) applies - 45 day payment window. Prioritize approval.",
            ebs_ap_status="NOT_STARTED",
            ebs_ap_ref=None,
            ebs_posted_at=None,
            approved_by=None,
            approved_at=None,
            rejected_by=None,
            rejected_at=None,
            rejection_reason=None,
            is_msme_supplier=True,
            msme_category="SMALL",
            msme_days_remaining=28,
            msme_due_date=future(28),
            msme_status="ON_TRACK",
            msme_penalty_amount=0,
            uploaded_by="Amit Sharma",
        ),
        Invoice(
            id=INV_IDS["INV005"],
            invoice_number="INV005",
            supplier_id=SUP_IDS["SUP007"],
            po_id=None,
            grn_id=None,
            invoice_date=past(15),
            due_date=past(2),
            subtotal=180000,
            gst_rate=12.0,
            gst_amount=21600,
            tds_rate=0.0,
            tds_amount=0,
            total_amount=201600,
            net_payable=201600,
            gstin_supplier="27AABCM7654E1ZQ",
            gstin_buyer="27AABCI1234D1ZP",
            hsn_sac="4911",
            irn="INV005-IRN-2024-MPH-78236",
            status="EXCEPTION",
            ocr_confidence=91.7,
            gstin_cache_status="VALID",
            gstin_validated_from_cache=True,
            gstr2b_itc_eligible=True,
            gstin_cache_age_hours=8.4,
            match_status="3WAY_MATCH_EXCEPTION",
            match_variance=0.0,
            match_exception_reason="No matching PO found. MSME MICRO supplier - payment overdue per Section 43B(h).",
            match_note="CRITICAL: MSME MICRO supplier payment is overdue. Section 43B(h) 45-day limit breached. Interest penalty may apply.",
            coding_agent_gl="6400",
            coding_agent_confidence=0.89,
            coding_agent_category="Printing & Marketing - Promotional Materials",
            fraud_flag=False,
            fraud_reasons=[],
            cash_opt_suggestion="URGENT: MSME MICRO payment overdue. Process immediately to minimize penalty under Section 43B(h).",
            ebs_ap_status="NOT_STARTED",
            ebs_ap_ref=None,
            ebs_posted_at=None,
            approved_by=None,
            approved_at=None,
            rejected_by=None,
            rejected_at=None,
            rejection_reason=None,
            is_msme_supplier=True,
            msme_category="MICRO",
            msme_days_remaining=-2,
            msme_due_date=past(2),
            msme_status="BREACHED",
            msme_penalty_amount=3326,
            uploaded_by="Vikram Patel",
        ),
        Invoice(
            id=INV_IDS["INV006"],
            invoice_number="INV006",
            supplier_id=SUP_IDS["SUP009"],
            po_id=None,
            grn_id=None,
            invoice_date=past(7),
            due_date=future(8),
            subtotal=425000,
            gst_rate=18.0,
            gst_amount=76500,
            tds_rate=0.0,
            tds_amount=0,
            total_amount=501500,
            net_payable=501500,
            gstin_supplier="27AABCS8765H1ZT",
            gstin_buyer="27AABCI1234D1ZP",
            hsn_sac="9403",
            irn=None,
            status="BLOCKED_FRAUD",
            ocr_confidence=72.4,
            gstin_cache_status="VALID",
            gstin_validated_from_cache=True,
            gstr2b_itc_eligible=True,
            gstin_cache_age_hours=3.1,
            match_status="BLOCKED_FRAUD",
            match_variance=0.0,
            match_exception_reason="Fraud detection triggered. Multiple anomalies detected.",
            match_note="Invoice blocked by AI Fraud Detection Agent. Duplicate invoice pattern detected. Amount deviates significantly from historical average.",
            coding_agent_gl="6600",
            coding_agent_confidence=0.65,
            coding_agent_category="Office Supplies - Furniture",
            fraud_flag=True,
            fraud_reasons=[
                "Duplicate invoice number pattern detected (similar to INV from 3 months ago)",
                "Amount 340% higher than supplier's historical average",
                "OCR confidence below 75% threshold",
                "Supplier risk score elevated (3.8/5.0)",
            ],
            cash_opt_suggestion="BLOCKED - Do not process. Pending fraud investigation.",
            ebs_ap_status="BLOCKED",
            ebs_ap_ref=None,
            ebs_posted_at=None,
            approved_by=None,
            approved_at=None,
            rejected_by=None,
            rejected_at=None,
            rejection_reason=None,
            is_msme_supplier=True,
            msme_category="MICRO",
            msme_days_remaining=8,
            msme_due_date=future(8),
            msme_status="AT_RISK",
            msme_penalty_amount=0,
            uploaded_by="Sunita Rao",
        ),
        Invoice(
            id=INV_IDS["INV007"],
            invoice_number="INV007",
            supplier_id=SUP_IDS["SUP011"],
            po_id=None,
            grn_id=None,
            invoice_date=past(1),
            due_date=future(29),
            subtotal=1650000,
            gst_rate=18.0,
            gst_amount=297000,
            tds_rate=2.0,
            tds_amount=33000,
            total_amount=1947000,
            net_payable=1914000,
            gstin_supplier="29AABCK5432K1ZW",
            gstin_buyer="27AABCI1234D1ZP",
            hsn_sac="998314",
            irn=None,
            status="CAPTURED",
            ocr_confidence=88.9,
            gstin_cache_status="PENDING",
            gstin_validated_from_cache=False,
            gstr2b_itc_eligible=None,
            gstin_cache_age_hours=None,
            match_status="PENDING",
            match_variance=None,
            match_exception_reason=None,
            match_note=None,
            coding_agent_gl=None,
            coding_agent_confidence=None,
            coding_agent_category=None,
            fraud_flag=False,
            fraud_reasons=[],
            cash_opt_suggestion=None,
            ebs_ap_status="NOT_STARTED",
            ebs_ap_ref=None,
            ebs_posted_at=None,
            approved_by=None,
            approved_at=None,
            rejected_by=None,
            rejected_at=None,
            rejection_reason=None,
            is_msme_supplier=True,
            msme_category="SMALL",
            msme_days_remaining=29,
            msme_due_date=future(29),
            msme_status="ON_TRACK",
            msme_penalty_amount=0,
            uploaded_by="Amit Sharma",
        ),
    ]


def build_gst_records() -> list[GSTRecord]:
    """15 GST cache records -- one per supplier GSTIN."""
    return [
        GSTRecord(
            id=_id(),
            gstin="27AATCM5678P1ZS",
            legal_name="TechMahindra Solutions Pvt Ltd",
            status="ACTIVE",
            state="Maharashtra",
            registration_type="Regular",
            last_gstr1_filed="Jan 2025",
            gstr2b_available=True,
            gstr2b_period="Jan 2025",
            gstr1_compliance="FILED",
            itc_eligible=True,
            last_synced=ts_dt(hours_ago=2),
            sync_source="CYGNET_BATCH",
            cache_hit_count=45,
            gstr2b_alert=None,
            itc_note="ITC eligible. GSTR-1 filed on time for last 12 months.",
        ),
        GSTRecord(
            id=_id(),
            gstin="29AATCW1234K1ZT",
            legal_name="Wipro Infrastructure Ltd",
            status="ACTIVE",
            state="Karnataka",
            registration_type="Regular",
            last_gstr1_filed="Jan 2025",
            gstr2b_available=True,
            gstr2b_period="Jan 2025",
            gstr1_compliance="FILED",
            itc_eligible=True,
            last_synced=ts_dt(hours_ago=3),
            sync_source="CYGNET_BATCH",
            cache_hit_count=32,
            gstr2b_alert=None,
            itc_note="ITC eligible. Consistent compliance record.",
        ),
        GSTRecord(
            id=_id(),
            gstin="27AABCR4321A1ZK",
            legal_name="Rajesh Office Suppliers",
            status="ACTIVE",
            state="Maharashtra",
            registration_type="Regular",
            last_gstr1_filed="Jan 2025",
            gstr2b_available=True,
            gstr2b_period="Jan 2025",
            gstr1_compliance="FILED",
            itc_eligible=True,
            last_synced=ts_dt(hours_ago=1),
            sync_source="CYGNET_BATCH",
            cache_hit_count=28,
            gstr2b_alert=None,
            itc_note="MSME MICRO vendor. ITC eligible. Monitor for late filings.",
        ),
        GSTRecord(
            id=_id(),
            gstin="07AABCI5678B1ZP",
            legal_name="ITC Business Solutions",
            status="ACTIVE",
            state="Delhi",
            registration_type="Regular",
            last_gstr1_filed="Jan 2025",
            gstr2b_available=True,
            gstr2b_period="Jan 2025",
            gstr1_compliance="FILED",
            itc_eligible=True,
            last_synced=ts_dt(hours_ago=4),
            sync_source="CYGNET_BATCH",
            cache_hit_count=18,
            gstr2b_alert=None,
            itc_note="ITC eligible. Large enterprise with strong compliance.",
        ),
        GSTRecord(
            id=_id(),
            gstin="24AATCG9876C1ZM",
            legal_name="Gujarat Tech Solutions",
            status="ACTIVE",
            state="Gujarat",
            registration_type="Regular",
            last_gstr1_filed="Dec 2024",
            gstr2b_available=True,
            gstr2b_period="Dec 2024",
            gstr1_compliance="DELAYED",
            itc_eligible=True,
            last_synced=ts_dt(hours_ago=5),
            sync_source="CYGNET_BATCH",
            cache_hit_count=15,
            gstr2b_alert="GSTR-1 filing delayed by 15 days for Jan 2025",
            itc_note="ITC eligible but monitor. GSTR-1 filing often delayed by 10-15 days.",
        ),
        GSTRecord(
            id=_id(),
            gstin="29AATCS2345D1ZN",
            legal_name="Sodexo Facilities India Pvt Ltd",
            status="ACTIVE",
            state="Karnataka",
            registration_type="Regular",
            last_gstr1_filed="Jan 2025",
            gstr2b_available=True,
            gstr2b_period="Jan 2025",
            gstr1_compliance="FILED",
            itc_eligible=True,
            last_synced=ts_dt(hours_ago=1),
            sync_source="CYGNET_BATCH",
            cache_hit_count=52,
            gstr2b_alert=None,
            itc_note="ITC eligible. Excellent compliance history.",
        ),
        GSTRecord(
            id=_id(),
            gstin="27AABCM7654E1ZQ",
            legal_name="Mumbai Print House",
            status="ACTIVE",
            state="Maharashtra",
            registration_type="Regular",
            last_gstr1_filed="Dec 2024",
            gstr2b_available=True,
            gstr2b_period="Dec 2024",
            gstr1_compliance="DELAYED",
            itc_eligible=True,
            last_synced=ts_dt(hours_ago=8),
            sync_source="CYGNET_BATCH",
            cache_hit_count=12,
            gstr2b_alert="GSTR-1 for Jan 2025 not yet filed",
            itc_note="ITC eligible but GSTR-1 filing consistency is poor. MSME MICRO vendor.",
        ),
        GSTRecord(
            id=_id(),
            gstin="07AATCD3456F1ZR",
            legal_name="Deloitte Advisory LLP",
            status="ACTIVE",
            state="Delhi",
            registration_type="Regular",
            last_gstr1_filed="Jan 2025",
            gstr2b_available=True,
            gstr2b_period="Jan 2025",
            gstr1_compliance="FILED",
            itc_eligible=True,
            last_synced=ts_dt(hours_ago=2),
            sync_source="CYGNET_BATCH",
            cache_hit_count=22,
            gstr2b_alert=None,
            itc_note="ITC eligible. Big 4 firm with impeccable compliance.",
        ),
        GSTRecord(
            id=_id(),
            gstin="27AABCS8765H1ZT",
            legal_name="Suresh Traders Pvt Ltd",
            status="ACTIVE",
            state="Maharashtra",
            registration_type="Regular",
            last_gstr1_filed="Nov 2024",
            gstr2b_available=True,
            gstr2b_period="Nov 2024",
            gstr1_compliance="PENDING",
            itc_eligible=False,
            last_synced=ts_dt(hours_ago=3),
            sync_source="CYGNET_BATCH",
            cache_hit_count=8,
            gstr2b_alert="GSTR-1 for Dec 2024 and Jan 2025 not filed. ITC at risk.",
            itc_note="ITC NOT eligible until GSTR-1 filings are current. Vendor has 2 months of pending returns.",
        ),
        GSTRecord(
            id=_id(),
            gstin="29AATCI3456J1ZV",
            legal_name="Infosys BPM Ltd",
            status="ACTIVE",
            state="Karnataka",
            registration_type="Regular",
            last_gstr1_filed="Jan 2025",
            gstr2b_available=True,
            gstr2b_period="Jan 2025",
            gstr1_compliance="FILED",
            itc_eligible=True,
            last_synced=ts_dt(hours_ago=1),
            sync_source="CYGNET_BATCH",
            cache_hit_count=38,
            gstr2b_alert=None,
            itc_note="ITC eligible. Large enterprise with automated filing.",
        ),
        GSTRecord(
            id=_id(),
            gstin="29AABCK5432K1ZW",
            legal_name="Karnataka Tech MSME Solutions",
            status="ACTIVE",
            state="Karnataka",
            registration_type="Regular",
            last_gstr1_filed="Jan 2025",
            gstr2b_available=True,
            gstr2b_period="Jan 2025",
            gstr1_compliance="FILED",
            itc_eligible=True,
            last_synced=ts_dt(hours_ago=6),
            sync_source="CYGNET_BATCH",
            cache_hit_count=10,
            gstr2b_alert=None,
            itc_note="ITC eligible. MSME SMALL vendor with good compliance.",
        ),
        GSTRecord(
            id=_id(),
            gstin="07AABCD6789M1ZY",
            legal_name="Delhi Stationery Hub",
            status="ACTIVE",
            state="Delhi",
            registration_type="Composition",
            last_gstr1_filed="Q3 FY2024-25",
            gstr2b_available=False,
            gstr2b_period=None,
            gstr1_compliance="FILED",
            itc_eligible=False,
            last_synced=ts_dt(hours_ago=12),
            sync_source="CYGNET_BATCH",
            cache_hit_count=3,
            gstr2b_alert="Composition dealer - GSTR-2B not applicable",
            itc_note="NOT eligible for ITC. Composition scheme dealer. Quarterly GSTR-4 filing.",
        ),
        GSTRecord(
            id=_id(),
            gstin="09AATCH6543G1ZS",
            legal_name="HCL Technologies Ltd",
            status="ACTIVE",
            state="Uttar Pradesh",
            registration_type="Regular",
            last_gstr1_filed="Jan 2025",
            gstr2b_available=True,
            gstr2b_period="Jan 2025",
            gstr1_compliance="FILED",
            itc_eligible=True,
            last_synced=ts_dt(hours_ago=2),
            sync_source="CYGNET_BATCH",
            cache_hit_count=25,
            gstr2b_alert=None,
            itc_note="ITC eligible. Major IT company with excellent compliance.",
        ),
        GSTRecord(
            id=_id(),
            gstin="07AATCK4567I1ZU",
            legal_name="KPMG India Pvt Ltd",
            status="ACTIVE",
            state="Delhi",
            registration_type="Regular",
            last_gstr1_filed="Jan 2025",
            gstr2b_available=True,
            gstr2b_period="Jan 2025",
            gstr1_compliance="FILED",
            itc_eligible=True,
            last_synced=ts_dt(hours_ago=2),
            sync_source="CYGNET_BATCH",
            cache_hit_count=20,
            gstr2b_alert=None,
            itc_note="ITC eligible. Big 4 firm with strong compliance record.",
        ),
        GSTRecord(
            id=_id(),
            gstin="07AATCM2345L1ZX",
            legal_name="Compass India Services Pvt Ltd",
            status="ACTIVE",
            state="Delhi",
            registration_type="Regular",
            last_gstr1_filed="Jan 2025",
            gstr2b_available=True,
            gstr2b_period="Jan 2025",
            gstr1_compliance="FILED",
            itc_eligible=True,
            last_synced=ts_dt(hours_ago=4),
            sync_source="CYGNET_BATCH",
            cache_hit_count=16,
            gstr2b_alert=None,
            itc_note="ITC eligible. Good compliance history.",
        ),
    ]


def build_ebs_events() -> list[EBSEvent]:
    """8 Oracle EBS integration events."""
    return [
        EBSEvent(
            id=EBS_IDS["EBS001"],
            event_code="EBS001",
            event_type="PO_COMMITMENT",
            entity_id="PO2024-001",
            entity_ref="EBS-PO-45231",
            description="PO commitment posted for IT Infrastructure Upgrade - TechMahindra",
            gl_account="6100",
            amount=12500000,
            ebs_module="GL",
            status="ACKNOWLEDGED",
            sent_at=ts_dt(days_ago=24),
            acknowledged_at=ts_dt(days_ago=24, hours_ago=0),
            ebs_ref="EBS-PO-45231",
            error_message=None,
        ),
        EBSEvent(
            id=EBS_IDS["EBS002"],
            event_code="EBS002",
            event_type="PO_COMMITMENT",
            entity_id="PO2024-002",
            entity_ref="EBS-PO-45232",
            description="PO commitment posted for Office Supplies Q3 - Rajesh Office Suppliers",
            gl_account="6600",
            amount=285000,
            ebs_module="GL",
            status="ACKNOWLEDGED",
            sent_at=ts_dt(days_ago=19),
            acknowledged_at=ts_dt(days_ago=19, hours_ago=0),
            ebs_ref="EBS-PO-45232",
            error_message=None,
        ),
        EBSEvent(
            id=EBS_IDS["EBS003"],
            event_code="EBS003",
            event_type="PO_COMMITMENT",
            entity_id="PO2024-003",
            entity_ref="EBS-PO-45233",
            description="PO commitment posted for Facility Management - Sodexo",
            gl_account="6200",
            amount=8500000,
            ebs_module="GL",
            status="ACKNOWLEDGED",
            sent_at=ts_dt(days_ago=17),
            acknowledged_at=ts_dt(days_ago=17, hours_ago=0),
            ebs_ref="EBS-PO-45233",
            error_message=None,
        ),
        EBSEvent(
            id=EBS_IDS["EBS004"],
            event_code="EBS004",
            event_type="INVOICE_POST",
            entity_id="INV001",
            entity_ref="EBS-AP-78234",
            description="Invoice posted to AP for TechMahindra IT Infrastructure",
            gl_account="6100",
            amount=14500000,
            ebs_module="AP",
            status="ACKNOWLEDGED",
            sent_at=ts_dt(days_ago=2),
            acknowledged_at=ts_dt(days_ago=2, hours_ago=0),
            ebs_ref="EBS-AP-78234",
            error_message=None,
        ),
        EBSEvent(
            id=EBS_IDS["EBS005"],
            event_code="EBS005",
            event_type="INVOICE_POST",
            entity_id="INV002",
            entity_ref=None,
            description="Invoice AP posting pending for Rajesh Office Suppliers (MSME)",
            gl_account="6600",
            amount=336300,
            ebs_module="AP",
            status="PENDING",
            sent_at=ts_dt(hours_ago=6),
            acknowledged_at=None,
            ebs_ref=None,
            error_message=None,
        ),
        EBSEvent(
            id=EBS_IDS["EBS006"],
            event_code="EBS006",
            event_type="GL_JOURNAL",
            entity_id="INV001",
            entity_ref="EBS-GL-J-12456",
            description="GL journal entry for TDS on TechMahindra invoice",
            gl_account="3100",
            amount=250000,
            ebs_module="GL",
            status="ACKNOWLEDGED",
            sent_at=ts_dt(days_ago=2),
            acknowledged_at=ts_dt(days_ago=2, hours_ago=0),
            ebs_ref="EBS-GL-J-12456",
            error_message=None,
        ),
        EBSEvent(
            id=EBS_IDS["EBS007"],
            event_code="EBS007",
            event_type="INVOICE_POST",
            entity_id="INV006",
            entity_ref=None,
            description="Invoice AP posting BLOCKED - fraud flag on Suresh Traders invoice",
            gl_account="6600",
            amount=501500,
            ebs_module="AP",
            status="FAILED",
            sent_at=ts_dt(days_ago=5),
            acknowledged_at=None,
            ebs_ref=None,
            error_message="BLOCKED: Fraud detection flag raised by AI agent. Manual review required before EBS posting.",
        ),
        EBSEvent(
            id=EBS_IDS["EBS008"],
            event_code="EBS008",
            event_type="FA_ADDITION",
            entity_id="PO2024-001",
            entity_ref="EBS-FA-9912",
            description="Fixed asset addition for 10x Dell PowerEdge servers from PO2024-001",
            gl_account="1500",
            amount=8500000,
            ebs_module="FA",
            status="ACKNOWLEDGED",
            sent_at=ts_dt(days_ago=4),
            acknowledged_at=ts_dt(days_ago=4, hours_ago=0),
            ebs_ref="EBS-FA-9912",
            error_message=None,
        ),
    ]


def build_ai_insights() -> list[AIInsight]:
    """7 AI agent insights."""
    return [
        AIInsight(
            id=AI_IDS["AI001"],
            insight_code="AI001",
            agent="InvoiceCodingAgent",
            invoice_id=INV_IDS["INV001"],
            supplier_id=SUP_IDS["SUP001"],
            insight_type="GL_CODING",
            confidence=0.96,
            recommendation="Auto-coded to GL 6100 (IT Services - Hardware & Infrastructure). High confidence based on supplier category and PO line items.",
            reasoning="Supplier TechMahindra is categorized as IT Services. PO2024-001 line items include servers and networking equipment. Historical coding for this supplier is consistently GL 6100. Confidence: 96%.",
            applied=True,
            applied_at=ts_dt(days_ago=4),
            status="APPLIED",
        ),
        AIInsight(
            id=AI_IDS["AI002"],
            insight_code="AI002",
            agent="FraudDetectionAgent",
            invoice_id=INV_IDS["INV006"],
            supplier_id=SUP_IDS["SUP009"],
            insight_type="FRAUD_ALERT",
            confidence=0.87,
            recommendation="BLOCK payment. Multiple fraud indicators detected: (1) Duplicate invoice pattern, (2) Amount 340% above historical average, (3) Low OCR confidence, (4) Elevated supplier risk score.",
            reasoning="Invoice INV006 from Suresh Traders triggers 4 fraud indicators. Historical average invoice from this supplier is INR 95,000 but this invoice is INR 425,000. OCR confidence of 72.4% suggests possible document manipulation. Supplier risk score is 3.8/5.0. Recommend immediate investigation.",
            applied=True,
            applied_at=ts_dt(days_ago=6),
            status="APPLIED",
        ),
        AIInsight(
            id=AI_IDS["AI003"],
            insight_code="AI003",
            agent="SLAPredictionAgent",
            invoice_id=INV_IDS["INV005"],
            supplier_id=SUP_IDS["SUP007"],
            insight_type="MSME_SLA_BREACH",
            confidence=0.95,
            recommendation="URGENT: MSME MICRO supplier Mumbai Print House payment has breached 45-day SLA. Invoice INV005 is 2 days overdue. Estimated penalty: INR 3,326. Escalate to Finance Head immediately.",
            reasoning="Invoice date: 15 days ago. MSME category: MICRO. Payment deadline was 45 days from invoice date but invoice has been in EXCEPTION status for 13 days without resolution. Section 43B(h) penalty applies at 3x bank rate on outstanding amount.",
            applied=False,
            applied_at=None,
            status="ESCALATED",
        ),
        AIInsight(
            id=AI_IDS["AI004"],
            insight_code="AI004",
            agent="CashOptimizationAgent",
            invoice_id=INV_IDS["INV003"],
            supplier_id=SUP_IDS["SUP006"],
            insight_type="EARLY_PAYMENT",
            confidence=0.82,
            recommendation="Early payment opportunity: Sodexo offers 1.5% discount for payment within 10 days. Potential saving: INR 36,975 on INV003. Current cash position supports early payment.",
            reasoning="Sodexo Facilities has offered 1.5% early payment discount historically. Invoice INV003 for INR 2,465,000 net payable. 10-day window from invoice date. Bank's current cash position is healthy with INR 2.3Cr surplus. Annualized return on early payment: 54.75%.",
            applied=False,
            applied_at=None,
            status="RECOMMENDED",
        ),
        AIInsight(
            id=AI_IDS["AI005"],
            insight_code="AI005",
            agent="SLAPredictionAgent",
            invoice_id=INV_IDS["INV004"],
            supplier_id=SUP_IDS["SUP005"],
            insight_type="MSME_SLA_RISK",
            confidence=0.78,
            recommendation="AT RISK: Gujarat Tech Solutions (MSME SMALL) invoice INV004 is in EXCEPTION status. 28 days remaining in 45-day window. Requires PO matching resolution before approval can proceed.",
            reasoning="Invoice INV004 has no matching PO and is stuck in EXCEPTION. MSME SMALL supplier with 45-day payment SLA. If not resolved within 17 days, manual approval workflow should be triggered to avoid SLA breach. Historical resolution time for non-PO exceptions: 12-15 days.",
            applied=False,
            applied_at=None,
            status="PENDING_ACTION",
        ),
        AIInsight(
            id=AI_IDS["AI006"],
            insight_code="AI006",
            agent="RiskAgent",
            invoice_id=None,
            supplier_id=SUP_IDS["SUP012"],
            insight_type="SUPPLIER_RISK",
            confidence=0.91,
            recommendation="Delhi Stationery Hub (SUP012) risk score elevated to 4.5/5.0. Composition scheme dealer - no ITC available. Vendor portal verification still pending. Recommend pausing new POs until verification complete.",
            reasoning="Supplier SUP012 has multiple risk factors: (1) Composition dealer - no ITC benefit, (2) Vendor portal status PENDING_VERIFICATION, (3) Risk score 4.5/5.0, (4) Onboarded only 45 days ago, (5) No completed transactions yet. Combined risk warrants hold on new business.",
            applied=False,
            applied_at=None,
            status="RECOMMENDED",
        ),
        AIInsight(
            id=AI_IDS["AI007"],
            insight_code="AI007",
            agent="InvoiceCodingAgent",
            invoice_id=INV_IDS["INV002"],
            supplier_id=SUP_IDS["SUP003"],
            insight_type="GL_CODING",
            confidence=0.92,
            recommendation="Auto-coded to GL 6600 (Administration - Office Supplies & Consumables). Matched against PO2024-002 line items.",
            reasoning="Supplier Rajesh Office Suppliers is categorized as Office Supplies. PO2024-002 contains stationery items. Department: ADMIN. Historical coding for office supplies from this supplier is GL 6600. Confidence: 92%.",
            applied=True,
            applied_at=ts_dt(days_ago=2),
            status="APPLIED",
        ),
    ]


def build_vendor_portal_events() -> list[VendorPortalEvent]:
    """6 vendor portal inbound events."""
    return [
        VendorPortalEvent(
            id=VPE_IDS["VPE001"],
            event_code="VPE001",
            event_type="vendor.onboarded",
            timestamp=ts_dt(days_ago=45),
            supplier_id="SUP012",
            supplier_name="Delhi Stationery Hub",
            payload={
                "gstin": "07AABCD6789M1ZY",
                "pan": "AABCD6789M",
                "category": "Office Supplies",
                "msme": True,
                "msme_category": "MICRO",
                "bank_verified": False,
            },
            processed=True,
            p2p_action="Created supplier record SUP012. Status: ACTIVE. Vendor portal verification: PENDING.",
        ),
        VendorPortalEvent(
            id=VPE_IDS["VPE002"],
            event_code="VPE002",
            event_type="vendor.bank_verified",
            timestamp=ts_dt(days_ago=30),
            supplier_id="SUP011",
            supplier_name="Karnataka Tech MSME Solutions",
            payload={
                "gstin": "29AABCK5432K1ZW",
                "bank_account": "9876543210011",
                "bank_name": "Canara Bank",
                "ifsc": "CNRB0011234",
                "verification_method": "penny_drop",
                "verified_at": ts(days_ago=30),
            },
            processed=True,
            p2p_action="Updated SUP011 bank details. Vendor portal status: VERIFIED.",
        ),
        VendorPortalEvent(
            id=VPE_IDS["VPE003"],
            event_code="VPE003",
            event_type="vendor.gstin_updated",
            timestamp=ts_dt(days_ago=20),
            supplier_id="SUP005",
            supplier_name="Gujarat Tech Solutions",
            payload={
                "old_gstin": "24AATCG9876C1ZM",
                "new_gstin": "24AATCG9876C1ZM",
                "reason": "Annual re-verification",
                "gstin_status": "ACTIVE",
                "verified_by": "Cygnet GSP",
            },
            processed=True,
            p2p_action="GSTIN re-verified for SUP005. No change in GSTIN. Cache refreshed.",
        ),
        VendorPortalEvent(
            id=VPE_IDS["VPE004"],
            event_code="VPE004",
            event_type="vendor.document_expired",
            timestamp=ts_dt(days_ago=5),
            supplier_id="SUP007",
            supplier_name="Mumbai Print House",
            payload={
                "document_type": "MSME_CERTIFICATE",
                "expired_on": past(5),
                "supplier_notified": True,
                "grace_period_days": 30,
            },
            processed=True,
            p2p_action="Alert raised for SUP007 MSME certificate expiry. Grace period: 30 days. Supplier notified via portal.",
        ),
        VendorPortalEvent(
            id=VPE_IDS["VPE005"],
            event_code="VPE005",
            event_type="vendor.risk_score_updated",
            timestamp=ts_dt(days_ago=2),
            supplier_id="SUP009",
            supplier_name="Suresh Traders Pvt Ltd",
            payload={
                "old_risk_score": 3.2,
                "new_risk_score": 3.8,
                "factors": [
                    "Late GST filing (2 months pending)",
                    "Bank account change request pending",
                    "Fraud flag on recent invoice",
                ],
            },
            processed=True,
            p2p_action="Updated SUP009 risk score from 3.2 to 3.8. Fraud investigation in progress for INV006.",
        ),
        VendorPortalEvent(
            id=VPE_IDS["VPE006"],
            event_code="VPE006",
            event_type="vendor.compliance_alert",
            timestamp=ts_dt(hours_ago=6),
            supplier_id="SUP003",
            supplier_name="Rajesh Office Suppliers",
            payload={
                "alert_type": "MSME_PAYMENT_DUE",
                "invoice_ref": "INV002",
                "amount": 336300,
                "due_date": future(12),
                "days_remaining": 12,
                "section": "43B(h)",
            },
            processed=False,
            p2p_action=None,
        ),
    ]


# ===================================================================
# MAIN SEED FUNCTION
# ===================================================================

async def seed():
    """Create all tables and insert seed data."""
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Check if already seeded
        try:
            result = await session.execute(text("SELECT COUNT(*) FROM suppliers"))
            count = result.scalar()
            if count and count > 0:
                print("Database already seeded. Use --force to re-seed.")
                return
        except Exception:
            # Table might not exist yet (shouldn't happen after create_all, but just in case)
            pass

        # ── Users ──────────────────────────────────────────────
        users = build_users()
        session.add_all(users)
        print(f"  + {len(users)} users")

        # ── Suppliers ──────────────────────────────────────────
        suppliers = build_suppliers()
        session.add_all(suppliers)
        print(f"  + {len(suppliers)} suppliers")

        # ── Budgets ────────────────────────────────────────────
        budgets = build_budgets()
        session.add_all(budgets)
        print(f"  + {len(budgets)} budgets")

        # ── Purchase Requests + Line Items ─────────────────────
        prs, pr_items = build_purchase_requests()
        session.add_all(prs)
        await session.flush()  # ensure PR ids are available for FK
        session.add_all(pr_items)
        print(f"  + {len(prs)} purchase requests ({len(pr_items)} line items)")

        # ── Purchase Orders + Line Items ───────────────────────
        pos, po_items = build_purchase_orders()
        session.add_all(pos)
        await session.flush()
        session.add_all(po_items)
        print(f"  + {len(pos)} purchase orders ({len(po_items)} line items)")

        # ── GRNs + Line Items ──────────────────────────────────
        grns, grn_items = build_grns()
        session.add_all(grns)
        await session.flush()
        session.add_all(grn_items)
        print(f"  + {len(grns)} goods receipt notes ({len(grn_items)} line items)")

        # ── Invoices ───────────────────────────────────────────
        invoices = build_invoices()
        session.add_all(invoices)
        print(f"  + {len(invoices)} invoices")

        # ── GST Cache ──────────────────────────────────────────
        gst_records = build_gst_records()
        session.add_all(gst_records)
        print(f"  + {len(gst_records)} GST cache records")

        # ── EBS Events ─────────────────────────────────────────
        ebs_events = build_ebs_events()
        session.add_all(ebs_events)
        print(f"  + {len(ebs_events)} EBS integration events")

        # ── AI Insights ────────────────────────────────────────
        ai_insights = build_ai_insights()
        session.add_all(ai_insights)
        print(f"  + {len(ai_insights)} AI insights")

        # ── Vendor Portal Events ───────────────────────────────
        vpe = build_vendor_portal_events()
        session.add_all(vpe)
        print(f"  + {len(vpe)} vendor portal events")

        # ── Commit ─────────────────────────────────────────────
        await session.commit()
        print("\nDatabase seeded successfully!")


async def force_seed():
    """Drop all tables and re-seed from scratch."""
    print("Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("Tables dropped. Re-seeding...")
    await seed()


# ===================================================================
# CLI entry point: python -m backend.seed [--force]
# ===================================================================

if __name__ == "__main__":
    if "--force" in sys.argv:
        asyncio.run(force_seed())
    else:
        asyncio.run(seed())
