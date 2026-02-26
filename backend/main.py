"""
IDFC P2P Platform — App Factory
================================

Modular monolith: mounts DB-backed module routers alongside a legacy
compatibility layer that preserves all prototype endpoints so the
frontend never breaks during migration.

Migrated modules (DB-backed):
  - /api/auth              → backend.modules.auth.routes
  - /api/suppliers         → backend.modules.suppliers.routes
  - /api/budgets           → backend.modules.budgets.routes
  - /api/purchase-requests → backend.modules.purchase_requests.routes
  - /api/purchase-orders   → backend.modules.purchase_orders.routes

Legacy (in-memory, will be migrated in future sprints):
  - /api/dashboard (hybrid — DB for migrated modules, in-memory for rest)
  - /api/invoices, /api/gst-cache, /api/msme-compliance,
    /api/oracle-ebs/events, /api/ai-agents/insights,
    /api/vendor-portal/events, /api/analytics/spend
"""

from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import engine
from backend.base_model import Base
from backend.dependencies import get_db
from backend.event_bus import Event, event_bus
from backend.exceptions import register_exception_handlers

# ── Module routers (DB-backed) ───────────────────────────────────
from backend.modules.auth.routes import router as auth_router
from backend.modules.suppliers.routes import router as suppliers_router
from backend.modules.budgets.routes import router as budgets_router
from backend.modules.purchase_requests.routes import router as pr_router
from backend.modules.purchase_orders.routes import router as po_router

# ── DB models needed by the hybrid dashboard ─────────────────────
from backend.modules.budgets.models import Budget
from backend.modules.purchase_requests.models import PurchaseRequest
from backend.modules.purchase_orders.models import PurchaseOrder
from backend.modules.suppliers.models import Supplier


# ─────────────────────────────────────────────
# LEGACY PROTOTYPE DATA (in-memory)
# Kept verbatim until each module is migrated.
# ─────────────────────────────────────────────

from typing import List, Optional, Any, Dict
from datetime import datetime, timedelta
import random
import copy


def ts(days_ago=0, hours_ago=0):
    d = datetime.now() - timedelta(days=days_ago, hours=hours_ago)
    return d.strftime("%Y-%m-%dT%H:%M:%S")

def future(days=0):
    d = datetime.now() + timedelta(days=days)
    return d.strftime("%Y-%m-%d")

def past(days=0):
    d = datetime.now() - timedelta(days=days)
    return d.strftime("%Y-%m-%d")


# ── Suppliers (kept for get_supplier() in invoice legacy endpoints) ──

SUPPLIERS = [
    {"id": "SUP001", "code": "SUP001", "legal_name": "TechMahindra Solutions Pvt Ltd",
     "gstin": "27AATCM5678P1ZS", "pan": "AATCM5678P", "state": "Maharashtra",
     "category": "IT Services", "is_msme": False, "msme_category": None,
     "bank_account": "XXXX8901", "bank_name": "HDFC Bank", "ifsc": "HDFC0001234",
     "payment_terms": 30, "risk_score": 2.1, "status": "ACTIVE",
     "vendor_portal_status": "VERIFIED", "contact_email": "ap@techmahindra.com",
     "onboarded_date": past(180), "last_synced_from_portal": ts(2)},
    {"id": "SUP002", "code": "SUP002", "legal_name": "Wipro Infrastructure Ltd",
     "gstin": "29AATCW1234K1ZT", "pan": "AATCW1234K", "state": "Karnataka",
     "category": "Facilities Management", "is_msme": False, "msme_category": None,
     "bank_account": "XXXX3456", "bank_name": "Axis Bank", "ifsc": "UTIB0000789",
     "payment_terms": 45, "risk_score": 1.8, "status": "ACTIVE",
     "vendor_portal_status": "VERIFIED", "contact_email": "billing@wiproinf.com",
     "onboarded_date": past(240), "last_synced_from_portal": ts(5)},
    {"id": "SUP003", "code": "SUP003", "legal_name": "Rajesh Office Suppliers",
     "gstin": "27AABCR4321A1ZK", "pan": "AABCR4321A", "state": "Maharashtra",
     "category": "Office Supplies", "is_msme": True, "msme_category": "MICRO",
     "bank_account": "XXXX7890", "bank_name": "SBI", "ifsc": "SBIN0001234",
     "payment_terms": 30, "risk_score": 3.4, "status": "ACTIVE",
     "vendor_portal_status": "VERIFIED", "contact_email": "rajesh@rajeshoffice.com",
     "onboarded_date": past(90), "last_synced_from_portal": ts(1)},
    {"id": "SUP004", "code": "SUP004", "legal_name": "ITC Business Solutions",
     "gstin": "07AABCI5678B1ZP", "pan": "AABCI5678B", "state": "Delhi",
     "category": "Professional Services", "is_msme": False, "msme_category": None,
     "bank_account": "XXXX2345", "bank_name": "ICICI Bank", "ifsc": "ICIC0000567",
     "payment_terms": 30, "risk_score": 1.5, "status": "ACTIVE",
     "vendor_portal_status": "VERIFIED", "contact_email": "invoices@itcbiz.com",
     "onboarded_date": past(300), "last_synced_from_portal": ts(3)},
    {"id": "SUP005", "code": "SUP005", "legal_name": "Gujarat Tech Solutions",
     "gstin": "24AATCG9876C1ZM", "pan": "AATCG9876C", "state": "Gujarat",
     "category": "IT Services", "is_msme": True, "msme_category": "SMALL",
     "bank_account": "XXXX5678", "bank_name": "Bank of Baroda", "ifsc": "BARB0001234",
     "payment_terms": 30, "risk_score": 2.8, "status": "ACTIVE",
     "vendor_portal_status": "VERIFIED", "contact_email": "gts@gujarattech.in",
     "onboarded_date": past(60), "last_synced_from_portal": ts(4)},
    {"id": "SUP006", "code": "SUP006", "legal_name": "Sodexo Facilities India Pvt Ltd",
     "gstin": "29AATCS2345D1ZN", "pan": "AATCS2345D", "state": "Karnataka",
     "category": "Facilities Management", "is_msme": False, "msme_category": None,
     "bank_account": "XXXX9012", "bank_name": "Citibank", "ifsc": "CITI0000123",
     "payment_terms": 30, "risk_score": 1.2, "status": "ACTIVE",
     "vendor_portal_status": "VERIFIED", "contact_email": "ar@sodexo.in",
     "onboarded_date": past(500), "last_synced_from_portal": ts(6)},
    {"id": "SUP007", "code": "SUP007", "legal_name": "Mumbai Print House",
     "gstin": "27AABCM7654E1ZQ", "pan": "AABCM7654E", "state": "Maharashtra",
     "category": "Printing & Marketing", "is_msme": True, "msme_category": "MICRO",
     "bank_account": "XXXX3456", "bank_name": "Union Bank", "ifsc": "UBIN0001234",
     "payment_terms": 15, "risk_score": 4.1, "status": "ACTIVE",
     "vendor_portal_status": "VERIFIED", "contact_email": "billing@mumbaiprint.com",
     "onboarded_date": past(45), "last_synced_from_portal": ts(0)},
    {"id": "SUP008", "code": "SUP008", "legal_name": "Deloitte Advisory LLP",
     "gstin": "07AATCD3456F1ZR", "pan": "AATCD3456F", "state": "Delhi",
     "category": "Consulting", "is_msme": False, "msme_category": None,
     "bank_account": "XXXX6789", "bank_name": "HSBC India", "ifsc": "HSBC0001234",
     "payment_terms": 30, "risk_score": 1.1, "status": "ACTIVE",
     "vendor_portal_status": "VERIFIED", "contact_email": "payments@deloitte.com",
     "onboarded_date": past(400), "last_synced_from_portal": ts(8)},
    {"id": "SUP009", "code": "SUP009", "legal_name": "Suresh Traders Pvt Ltd",
     "gstin": "27AABCS8765H1ZT", "pan": "AABCS8765H", "state": "Maharashtra",
     "category": "Office Supplies", "is_msme": True, "msme_category": "MICRO",
     "bank_account": "XXXX0123", "bank_name": "Punjab National Bank", "ifsc": "PUNB0001234",
     "payment_terms": 30, "risk_score": 3.8, "status": "ACTIVE",
     "vendor_portal_status": "VERIFIED", "contact_email": "suresh@sureshtraders.com",
     "onboarded_date": past(120), "last_synced_from_portal": ts(2)},
    {"id": "SUP010", "code": "SUP010", "legal_name": "Infosys BPM Ltd",
     "gstin": "29AATCI3456J1ZV", "pan": "AATCI3456J", "state": "Karnataka",
     "category": "IT Services", "is_msme": False, "msme_category": None,
     "bank_account": "XXXX4567", "bank_name": "Kotak Bank", "ifsc": "KKBK0001234",
     "payment_terms": 30, "risk_score": 1.3, "status": "ACTIVE",
     "vendor_portal_status": "VERIFIED", "contact_email": "payments@infosysbpm.com",
     "onboarded_date": past(600), "last_synced_from_portal": ts(12)},
    {"id": "SUP011", "code": "SUP011", "legal_name": "Karnataka Tech MSME Solutions",
     "gstin": "29AABCK5432K1ZW", "pan": "AABCK5432K", "state": "Karnataka",
     "category": "IT Services", "is_msme": True, "msme_category": "SMALL",
     "bank_account": "XXXX7891", "bank_name": "Canara Bank", "ifsc": "CNRB0001234",
     "payment_terms": 30, "risk_score": 3.2, "status": "ACTIVE",
     "vendor_portal_status": "VERIFIED", "contact_email": "billing@karntech.in",
     "onboarded_date": past(75), "last_synced_from_portal": ts(3)},
    {"id": "SUP012", "code": "SUP012", "legal_name": "Delhi Stationery Hub",
     "gstin": "07AABCD6789M1ZY", "pan": "AABCD6789M", "state": "Delhi",
     "category": "Office Supplies", "is_msme": True, "msme_category": "MICRO",
     "bank_account": "XXXX2345", "bank_name": "Indian Bank", "ifsc": "IDIB0001234",
     "payment_terms": 15, "risk_score": 4.5, "status": "ACTIVE",
     "vendor_portal_status": "PENDING_VERIFICATION", "contact_email": "dsh@delhistat.com",
     "onboarded_date": past(10), "last_synced_from_portal": ts(0)},
    {"id": "SUP013", "code": "SUP013", "legal_name": "HCL Technologies Ltd",
     "gstin": "09AATCH6543G1ZS", "pan": "AATCH6543G", "state": "Uttar Pradesh",
     "category": "IT Services", "is_msme": False, "msme_category": None,
     "bank_account": "XXXX6781", "bank_name": "Yes Bank", "ifsc": "YESB0001234",
     "payment_terms": 45, "risk_score": 1.6, "status": "ACTIVE",
     "vendor_portal_status": "VERIFIED", "contact_email": "ap@hcl.com",
     "onboarded_date": past(365), "last_synced_from_portal": ts(24)},
    {"id": "SUP014", "code": "SUP014", "legal_name": "KPMG India Pvt Ltd",
     "gstin": "07AATCK4567I1ZU", "pan": "AATCK4567I", "state": "Delhi",
     "category": "Consulting", "is_msme": False, "msme_category": None,
     "bank_account": "XXXX9012", "bank_name": "Deutsche Bank", "ifsc": "DEUT0000123",
     "payment_terms": 30, "risk_score": 1.0, "status": "ACTIVE",
     "vendor_portal_status": "VERIFIED", "contact_email": "invoices@kpmg.com",
     "onboarded_date": past(450), "last_synced_from_portal": ts(4)},
    {"id": "SUP015", "code": "SUP015", "legal_name": "Compass India Services Pvt Ltd",
     "gstin": "07AATCM2345L1ZX", "pan": "AATCM2345L", "state": "Delhi",
     "category": "Facilities Management", "is_msme": False, "msme_category": None,
     "bank_account": "XXXX5670", "bank_name": "Standard Chartered", "ifsc": "SCBL0001234",
     "payment_terms": 30, "risk_score": 1.7, "status": "ACTIVE",
     "vendor_portal_status": "VERIFIED", "contact_email": "billing@compassindia.com",
     "onboarded_date": past(280), "last_synced_from_portal": ts(7)},
]

INVOICES = [
    {"id": "INV001", "invoice_number": "TM/2024/8821",
     "supplier_id": "SUP001", "supplier_name": "TechMahindra Solutions Pvt Ltd",
     "po_id": "PO2024-001", "grn_id": "GRN2024-001",
     "invoice_date": past(4), "due_date": future(26),
     "subtotal": 4500000, "gst_rate": 18, "gst_amount": 810000, "tds_rate": 2,
     "tds_amount": 90000, "total_amount": 5310000, "net_payable": 5220000,
     "gstin_supplier": "27AATCM5678P1ZS", "gstin_buyer": "27AAACI1234D1ZW",
     "hsn_sac": "9983", "irn": "a5f8d2c1e9b3741068f3cd5a2b67e4d910f2e853bc7a49d6213085f7c4e91b20",
     "status": "POSTED_TO_EBS", "ocr_confidence": 97.3,
     "gstin_cache_status": "ACTIVE", "gstin_validated_from_cache": True,
     "gstr2b_itc_eligible": True, "gstin_cache_age_hours": 3.7,
     "match_status": "3WAY_MATCH_PASSED", "match_variance": 0.0,
     "coding_agent_gl": "6100-003", "coding_agent_confidence": 94.2,
     "coding_agent_category": "IT Services",
     "fraud_flag": False, "fraud_reasons": [],
     "cash_opt_suggestion": "Pay on Day 20 (save ₹22,500 via early payment discount)",
     "ebs_ap_status": "POSTED", "ebs_ap_ref": "EBS-AP-78234",
     "ebs_posted_at": ts(1),
     "approved_by": "Priya Menon", "approved_at": ts(2),
     "is_msme_supplier": False, "msme_days_remaining": None,
     "created_at": ts(4), "uploaded_by": "AP Team"},
    {"id": "INV002", "invoice_number": "ROS/SEP/2024/143",
     "supplier_id": "SUP003", "supplier_name": "Rajesh Office Suppliers",
     "po_id": "PO2024-002", "grn_id": "GRN2024-002",
     "invoice_date": past(6), "due_date": future(24),
     "subtotal": 155000, "gst_rate": 5, "gst_amount": 7750, "tds_rate": 1,
     "tds_amount": 1550, "total_amount": 162750, "net_payable": 161200,
     "gstin_supplier": "27AABCR4321A1ZK", "gstin_buyer": "27AAACI1234D1ZW",
     "hsn_sac": "4820", "irn": "b6a9e3f2c1d4852179g4de6b3c78f5e021g3f964cd8b50e7324196g8d5f02c31",
     "status": "PENDING_APPROVAL", "ocr_confidence": 91.8,
     "gstin_cache_status": "ACTIVE", "gstin_validated_from_cache": True,
     "gstr2b_itc_eligible": True, "gstin_cache_age_hours": 2.1,
     "match_status": "3WAY_MATCH_EXCEPTION", "match_variance": 4.2,
     "match_exception_reason": "Invoice for 50 boxes of pens; only 30 GRN-confirmed. Markers (qty 100) not received — not invoiced. Balance billing expected.",
     "coding_agent_gl": "6600-001", "coding_agent_confidence": 88.5,
     "coding_agent_category": "Office Supplies",
     "fraud_flag": False, "fraud_reasons": [],
     "cash_opt_suggestion": "MSME vendor — pay within 24 days to avoid Sec 43B(h) breach",
     "ebs_ap_status": "PENDING", "ebs_ap_ref": None,
     "approved_by": None, "approved_at": None,
     "is_msme_supplier": True, "msme_category": "MICRO",
     "msme_days_remaining": 24, "msme_due_date": future(24),
     "msme_status": "ON_TRACK",
     "created_at": ts(6), "uploaded_by": "Sunita Rao"},
    {"id": "INV003", "invoice_number": "TM/2024/8821",
     "supplier_id": "SUP001", "supplier_name": "TechMahindra Solutions Pvt Ltd",
     "po_id": "PO2024-001", "grn_id": "GRN2024-001",
     "invoice_date": past(4), "due_date": future(26),
     "subtotal": 4500000, "gst_rate": 18, "gst_amount": 810000, "tds_rate": 2,
     "tds_amount": 90000, "total_amount": 5310000, "net_payable": 5220000,
     "gstin_supplier": "27AATCM5678P1ZS", "gstin_buyer": "27AAACI1234D1ZW",
     "hsn_sac": "9983", "irn": None, "status": "REJECTED", "ocr_confidence": 96.1,
     "gstin_cache_status": "ACTIVE", "gstin_validated_from_cache": True,
     "gstr2b_itc_eligible": True, "gstin_cache_age_hours": 3.7,
     "match_status": "BLOCKED_FRAUD", "match_variance": 0.0,
     "coding_agent_gl": "6100-003", "coding_agent_confidence": 94.1,
     "coding_agent_category": "IT Services",
     "fraud_flag": True,
     "fraud_reasons": [
         "Duplicate invoice number TM/2024/8821 — already processed as INV001",
         "Same PO reference, same amount, same date",
         "Submitted 2 days after original payment"
     ],
     "cash_opt_suggestion": None,
     "ebs_ap_status": "BLOCKED", "ebs_ap_ref": None,
     "approved_by": None, "approved_at": None,
     "rejected_by": "Fraud Detection Agent (Auto)", "rejected_at": ts(2),
     "is_msme_supplier": False, "msme_days_remaining": None,
     "created_at": ts(2), "uploaded_by": "AP Team"},
    {"id": "INV004", "invoice_number": "KPMG/2024/IDFC/092",
     "supplier_id": "SUP014", "supplier_name": "KPMG India Pvt Ltd",
     "po_id": "PO2024-003", "grn_id": "GRN2024-003",
     "invoice_date": past(1), "due_date": future(29),
     "subtotal": 1400000, "gst_rate": 18, "gst_amount": 252000, "tds_rate": 10,
     "tds_amount": 140000, "total_amount": 1652000, "net_payable": 1512000,
     "gstin_supplier": "07AATCK4567I1ZU", "gstin_buyer": "27AAACI1234D1ZW",
     "hsn_sac": "9983", "irn": "c7b0f4e3d2e5963280h5ef7c4d89g6f132h4g075de9c61f8435207h9e6g13d42",
     "status": "MATCHED", "ocr_confidence": 98.2,
     "gstin_cache_status": "ACTIVE", "gstin_validated_from_cache": True,
     "gstr2b_itc_eligible": True, "gstin_cache_age_hours": 4.3,
     "match_status": "3WAY_MATCH_PASSED", "match_variance": 0.0,
     "match_note": "Invoice covers milestones 1 & 2. Milestone 3 billing pending (Month 3 hypercare).",
     "coding_agent_gl": "6300-005", "coding_agent_confidence": 96.7,
     "coding_agent_category": "Professional Services — Consulting",
     "fraud_flag": False, "fraud_reasons": [],
     "cash_opt_suggestion": "Standard 30-day terms. No early payment benefit identified.",
     "ebs_ap_status": "PENDING", "ebs_ap_ref": None,
     "approved_by": None, "approved_at": None,
     "is_msme_supplier": False, "msme_days_remaining": None,
     "created_at": ts(1), "uploaded_by": "Meera Iyer"},
    {"id": "INV005", "invoice_number": "GTS/2024/0456",
     "supplier_id": "SUP005", "supplier_name": "Gujarat Tech Solutions",
     "po_id": None, "grn_id": None,
     "invoice_date": past(38), "due_date": future(7),
     "subtotal": 480000, "gst_rate": 18, "gst_amount": 86400, "tds_rate": 2,
     "tds_amount": 9600, "total_amount": 566400, "net_payable": 556800,
     "gstin_supplier": "24AATCG9876C1ZM", "gstin_buyer": "27AAACI1234D1ZW",
     "hsn_sac": "9983", "irn": "d8c1e5f4e3f6074391i6fg8d5e90h7g243i5h186ef0d72g9546318i0f7h24e53",
     "status": "PENDING_APPROVAL", "ocr_confidence": 89.4,
     "gstin_cache_status": "ACTIVE", "gstin_validated_from_cache": True,
     "gstr2b_itc_eligible": True, "gstin_cache_age_hours": 5.1,
     "match_status": "2WAY_MATCH_PASSED", "match_variance": 0.0,
     "coding_agent_gl": "6100-003", "coding_agent_confidence": 91.3,
     "coding_agent_category": "IT Services",
     "fraud_flag": False, "fraud_reasons": [],
     "cash_opt_suggestion": "CRITICAL: MSME supplier — 45-day limit expires in 7 days. Initiate payment IMMEDIATELY to avoid Sec 43B(h) penalty.",
     "ebs_ap_status": "PENDING", "ebs_ap_ref": None,
     "approved_by": None, "approved_at": None,
     "is_msme_supplier": True, "msme_category": "SMALL",
     "msme_days_remaining": 7, "msme_due_date": future(7),
     "msme_status": "AT_RISK",
     "created_at": ts(38), "uploaded_by": "AP Team"},
    {"id": "INV006", "invoice_number": "MPH/AUG/2024/078",
     "supplier_id": "SUP007", "supplier_name": "Mumbai Print House",
     "po_id": None, "grn_id": None,
     "invoice_date": past(52), "due_date": past(7),
     "subtotal": 320000, "gst_rate": 5, "gst_amount": 16000, "tds_rate": 1,
     "tds_amount": 3200, "total_amount": 336000, "net_payable": 332800,
     "gstin_supplier": "27AABCM7654E1ZQ", "gstin_buyer": "27AAACI1234D1ZW",
     "hsn_sac": "4911", "irn": "e9d2f6g5f4g7185402j7gh9e6f01i8h354j6i297fg1e83h0657429j1g8i35f64",
     "status": "APPROVED", "ocr_confidence": 85.6,
     "gstin_cache_status": "ACTIVE", "gstin_validated_from_cache": True,
     "gstr2b_itc_eligible": False, "gstin_cache_age_hours": 1.2,
     "match_status": "2WAY_MATCH_PASSED", "match_variance": 0.0,
     "coding_agent_gl": "6400-003", "coding_agent_confidence": 87.9,
     "coding_agent_category": "Printing & Marketing",
     "fraud_flag": False, "fraud_reasons": [],
     "cash_opt_suggestion": "BREACH: MSME 45-day limit exceeded by 7 days. Compounded interest penalty applicable: ₹8,428. Raise payment immediately.",
     "ebs_ap_status": "PENDING", "ebs_ap_ref": None,
     "approved_by": "Rohan Joshi", "approved_at": ts(3),
     "is_msme_supplier": True, "msme_category": "MICRO",
     "msme_days_remaining": -7, "msme_due_date": past(7),
     "msme_status": "BREACHED", "msme_penalty_amount": 8428,
     "created_at": ts(52), "uploaded_by": "AP Team"},
    {"id": "INV007", "invoice_number": "SOD/2024/INV/3421",
     "supplier_id": "SUP006", "supplier_name": "Sodexo Facilities India Pvt Ltd",
     "po_id": None, "grn_id": None,
     "invoice_date": past(0), "due_date": future(30),
     "subtotal": 285000, "gst_rate": 18, "gst_amount": 51300, "tds_rate": 2,
     "tds_amount": 5700, "total_amount": 336300, "net_payable": 330600,
     "gstin_supplier": "29AATCS2345D1ZN", "gstin_buyer": "27AAACI1234D1ZW",
     "hsn_sac": "9985", "irn": None, "status": "CAPTURED", "ocr_confidence": None,
     "gstin_cache_status": "ACTIVE", "gstin_validated_from_cache": False,
     "gstr2b_itc_eligible": None, "gstin_cache_age_hours": None,
     "match_status": "PENDING", "match_variance": None,
     "coding_agent_gl": None, "coding_agent_confidence": None,
     "coding_agent_category": None,
     "fraud_flag": False, "fraud_reasons": [],
     "cash_opt_suggestion": None,
     "ebs_ap_status": "NOT_STARTED", "ebs_ap_ref": None,
     "approved_by": None, "approved_at": None,
     "is_msme_supplier": False, "msme_days_remaining": None,
     "created_at": ts(0), "uploaded_by": "Deepak Nair"},
]

GST_CACHE = [
    {"gstin": "27AATCM5678P1ZS", "legal_name": "TechMahindra Solutions Pvt Ltd", "status": "ACTIVE", "state": "Maharashtra", "registration_type": "Regular", "last_gstr1_filed": "Aug 2024", "gstr2b_available": True, "gstr2b_period": "Aug 2024", "gstr1_compliance": "FILED", "itc_eligible": True, "last_synced": ts(3, 42), "sync_source": "CYGNET_BATCH", "cache_hit_count": 47},
    {"gstin": "29AATCW1234K1ZT", "legal_name": "Wipro Infrastructure Ltd", "status": "ACTIVE", "state": "Karnataka", "registration_type": "Regular", "last_gstr1_filed": "Aug 2024", "gstr2b_available": True, "gstr2b_period": "Aug 2024", "gstr1_compliance": "FILED", "itc_eligible": True, "last_synced": ts(4, 15), "sync_source": "CYGNET_BATCH", "cache_hit_count": 23},
    {"gstin": "27AABCR4321A1ZK", "legal_name": "Rajesh Office Suppliers", "status": "ACTIVE", "state": "Maharashtra", "registration_type": "Composition", "last_gstr1_filed": "Aug 2024", "gstr2b_available": True, "gstr2b_period": "Aug 2024", "gstr1_compliance": "FILED", "itc_eligible": True, "last_synced": ts(2, 5), "sync_source": "CYGNET_BATCH", "cache_hit_count": 19},
    {"gstin": "07AABCI5678B1ZP", "legal_name": "ITC Business Solutions", "status": "ACTIVE", "state": "Delhi", "registration_type": "Regular", "last_gstr1_filed": "Aug 2024", "gstr2b_available": True, "gstr2b_period": "Aug 2024", "gstr1_compliance": "FILED", "itc_eligible": True, "last_synced": ts(5, 20), "sync_source": "CYGNET_BATCH", "cache_hit_count": 12},
    {"gstin": "24AATCG9876C1ZM", "legal_name": "Gujarat Tech Solutions", "status": "ACTIVE", "state": "Gujarat", "registration_type": "Regular", "last_gstr1_filed": "Jul 2024", "gstr2b_available": False, "gstr2b_period": None, "gstr1_compliance": "PENDING", "itc_eligible": False, "last_synced": ts(4, 30), "sync_source": "CYGNET_BATCH", "cache_hit_count": 8, "gstr2b_alert": "GSTR-2B for Aug 2024 not yet available — ITC unconfirmed"},
    {"gstin": "29AATCS2345D1ZN", "legal_name": "Sodexo Facilities India Pvt Ltd", "status": "ACTIVE", "state": "Karnataka", "registration_type": "Regular", "last_gstr1_filed": "Aug 2024", "gstr2b_available": True, "gstr2b_period": "Aug 2024", "gstr1_compliance": "FILED", "itc_eligible": True, "last_synced": ts(1, 50), "sync_source": "CYGNET_BATCH", "cache_hit_count": 31},
    {"gstin": "27AABCM7654E1ZQ", "legal_name": "Mumbai Print House", "status": "ACTIVE", "state": "Maharashtra", "registration_type": "Composition", "last_gstr1_filed": "Aug 2024", "gstr2b_available": True, "gstr2b_period": "Aug 2024", "gstr1_compliance": "FILED", "itc_eligible": False, "last_synced": ts(0, 45), "sync_source": "CYGNET_LIVE", "cache_hit_count": 6, "itc_note": "Composition dealer — ITC not available"},
    {"gstin": "07AATCD3456F1ZR", "legal_name": "Deloitte Advisory LLP", "status": "ACTIVE", "state": "Delhi", "registration_type": "Regular", "last_gstr1_filed": "Aug 2024", "gstr2b_available": True, "gstr2b_period": "Aug 2024", "gstr1_compliance": "FILED", "itc_eligible": True, "last_synced": ts(6, 10), "sync_source": "CYGNET_BATCH", "cache_hit_count": 5},
    {"gstin": "27AABCS8765H1ZT", "legal_name": "Suresh Traders Pvt Ltd", "status": "ACTIVE", "state": "Maharashtra", "registration_type": "Regular", "last_gstr1_filed": "Jul 2024", "gstr2b_available": False, "gstr2b_period": None, "gstr1_compliance": "DELAYED", "itc_eligible": False, "last_synced": ts(3, 20), "sync_source": "CYGNET_BATCH", "cache_hit_count": 14, "gstr2b_alert": "GSTR-1 for Aug 2024 not filed — raise with vendor"},
    {"gstin": "29AATCI3456J1ZV", "legal_name": "Infosys BPM Ltd", "status": "ACTIVE", "state": "Karnataka", "registration_type": "Regular", "last_gstr1_filed": "Aug 2024", "gstr2b_available": True, "gstr2b_period": "Aug 2024", "gstr1_compliance": "FILED", "itc_eligible": True, "last_synced": ts(2, 30), "sync_source": "CYGNET_BATCH", "cache_hit_count": 29},
    {"gstin": "29AABCK5432K1ZW", "legal_name": "Karnataka Tech MSME Solutions", "status": "ACTIVE", "state": "Karnataka", "registration_type": "Regular", "last_gstr1_filed": "Aug 2024", "gstr2b_available": True, "gstr2b_period": "Aug 2024", "gstr1_compliance": "FILED", "itc_eligible": True, "last_synced": ts(3, 55), "sync_source": "CYGNET_BATCH", "cache_hit_count": 11},
    {"gstin": "07AABCD6789M1ZY", "legal_name": "Delhi Stationery Hub", "status": "ACTIVE", "state": "Delhi", "registration_type": "Regular", "last_gstr1_filed": "Aug 2024", "gstr2b_available": False, "gstr2b_period": None, "gstr1_compliance": "PENDING", "itc_eligible": False, "last_synced": ts(0, 10), "sync_source": "CYGNET_BATCH", "cache_hit_count": 2, "gstr2b_alert": "GSTR-2B for Aug 2024 not yet available — await next sync"},
    {"gstin": "09AATCH6543G1ZS", "legal_name": "HCL Technologies Ltd", "status": "ACTIVE", "state": "Uttar Pradesh", "registration_type": "Regular", "last_gstr1_filed": "Aug 2024", "gstr2b_available": True, "gstr2b_period": "Aug 2024", "gstr1_compliance": "FILED", "itc_eligible": True, "last_synced": ts(5, 0), "sync_source": "CYGNET_BATCH", "cache_hit_count": 18},
    {"gstin": "07AATCK4567I1ZU", "legal_name": "KPMG India Pvt Ltd", "status": "ACTIVE", "state": "Delhi", "registration_type": "Regular", "last_gstr1_filed": "Aug 2024", "gstr2b_available": True, "gstr2b_period": "Aug 2024", "gstr1_compliance": "FILED", "itc_eligible": True, "last_synced": ts(4, 5), "sync_source": "CYGNET_BATCH", "cache_hit_count": 9},
    {"gstin": "07AATCM2345L1ZX", "legal_name": "Compass India Services Pvt Ltd", "status": "ACTIVE", "state": "Delhi", "registration_type": "Regular", "last_gstr1_filed": "Aug 2024", "gstr2b_available": True, "gstr2b_period": "Aug 2024", "gstr1_compliance": "FILED", "itc_eligible": True, "last_synced": ts(3, 0), "sync_source": "CYGNET_BATCH", "cache_hit_count": 7},
]

EBS_EVENTS = [
    {"id": "EBS001", "event_type": "PO_COMMITMENT", "entity_id": "PO2024-001", "entity_ref": "PO2024-001", "description": "PO Commitment → GL Encumbrance", "gl_account": "6100-003", "amount": 4500000, "ebs_module": "GL", "status": "ACKNOWLEDGED", "sent_at": ts(18), "acknowledged_at": ts(18, 0), "ebs_ref": "EBS-GL-45823", "error_message": None},
    {"id": "EBS002", "event_type": "PO_COMMITMENT", "entity_id": "PO2024-002", "entity_ref": "PO2024-002", "description": "PO Commitment → GL Encumbrance", "gl_account": "6600-001", "amount": 185000, "ebs_module": "GL", "status": "ACKNOWLEDGED", "sent_at": ts(13), "acknowledged_at": ts(13, 0), "ebs_ref": "EBS-GL-45891", "error_message": None},
    {"id": "EBS003", "event_type": "PO_COMMITMENT", "entity_id": "PO2024-003", "entity_ref": "PO2024-003", "description": "PO Commitment → GL Encumbrance", "gl_account": "6300-005", "amount": 1800000, "ebs_module": "GL", "status": "ACKNOWLEDGED", "sent_at": ts(22), "acknowledged_at": ts(22, 0), "ebs_ref": "EBS-GL-45901", "error_message": None},
    {"id": "EBS004", "event_type": "INVOICE_POST", "entity_id": "INV001", "entity_ref": "TM/2024/8821", "description": "Invoice → AP Open Interface (Approved)", "gl_account": "6100-003", "amount": 5220000, "ebs_module": "AP", "status": "ACKNOWLEDGED", "sent_at": ts(2), "acknowledged_at": ts(1, 58), "ebs_ref": "EBS-AP-78234", "error_message": None},
    {"id": "EBS005", "event_type": "INVOICE_POST", "entity_id": "INV006", "entity_ref": "MPH/AUG/2024/078", "description": "Invoice → AP Open Interface (MSME BREACH)", "gl_account": "6400-003", "amount": 332800, "ebs_module": "AP", "status": "FAILED", "sent_at": ts(3), "acknowledged_at": None, "ebs_ref": None, "error_message": "ORA-20001: Duplicate invoice number in AP. Possible re-submission. Manual review required."},
    {"id": "EBS006", "event_type": "GL_JOURNAL", "entity_id": "PERIOD-SEP24", "entity_ref": "PERIOD-SEP24", "description": "Period Accrual Journal — Sep 2024", "gl_account": "MULTI", "amount": 6485000, "ebs_module": "GL", "status": "ACKNOWLEDGED", "sent_at": ts(48), "acknowledged_at": ts(47, 55), "ebs_ref": "EBS-GL-46012", "error_message": None},
    {"id": "EBS007", "event_type": "FA_ADDITION", "entity_id": "PO2024-001", "entity_ref": "PO2024-001", "description": "Fixed Asset Addition — AWS Infrastructure", "gl_account": "1500-001", "amount": 4500000, "ebs_module": "FA", "status": "PENDING", "sent_at": ts(1), "acknowledged_at": None, "ebs_ref": None, "error_message": None},
    {"id": "EBS008", "event_type": "INVOICE_POST", "entity_id": "INV004", "entity_ref": "KPMG/2024/IDFC/092", "description": "Invoice → AP Open Interface (Queued post approval)", "gl_account": "6300-005", "amount": 1512000, "ebs_module": "AP", "status": "PENDING", "sent_at": None, "acknowledged_at": None, "ebs_ref": None, "error_message": None},
]

AI_INSIGHTS = [
    {"id": "AI001", "agent": "InvoiceCodingAgent", "invoice_id": "INV001", "type": "GL_CODING", "confidence": 94.2, "recommendation": "GL Account: 6100-003 (IT Services — Infrastructure)", "reasoning": "Vendor category IT Services + HSN 9983 + historical PO pattern (87% of TechMahindra invoices → 6100-003)", "applied": True, "applied_at": ts(4), "status": "APPLIED"},
    {"id": "AI002", "agent": "FraudDetectionAgent", "invoice_id": "INV003", "type": "FRAUD_ALERT", "confidence": 99.1, "recommendation": "AUTO-REJECT: Duplicate invoice detected", "reasoning": "Invoice number TM/2024/8821 exists in INV001 (paid). Same supplier, same PO, same amount, date within 2 days. Velocity: 2nd submission for same PO within 48h.", "applied": True, "applied_at": ts(2), "status": "APPLIED"},
    {"id": "AI003", "agent": "SLAPredictionAgent", "invoice_id": "INV005", "type": "MSME_SLA_RISK", "confidence": 97.8, "recommendation": "ESCALATE: Gujarat Tech Solutions MSME invoice due in 7 days", "reasoning": "Invoice age 38 days. MSME SMALL category. Sec 43B(h) 45-day limit = 7 days remaining. Approval SLA historically 3 days. Payment run cycle T+2. Net runway: 2 days to approve.", "applied": False, "applied_at": None, "status": "PENDING_ACTION"},
    {"id": "AI004", "agent": "SLAPredictionAgent", "invoice_id": "INV006", "type": "MSME_SLA_BREACH", "confidence": 100.0, "recommendation": "BREACH CONFIRMED: Mumbai Print House — 7 days past 45-day MSME limit", "reasoning": "Invoice date Aug 8. 45-day limit = Sep 22. Today = Sep 29. Breach: 7 days. Penalty: ₹8,428 (compound interest @ 3x RBI rate). Immediate payment required.", "applied": True, "applied_at": ts(3), "status": "ESCALATED"},
    {"id": "AI005", "agent": "CashOptimizationAgent", "invoice_id": "INV001", "type": "EARLY_PAYMENT", "confidence": 78.3, "recommendation": "Early payment on Day 20 saves ₹22,500 via 0.5% discount", "reasoning": "TechMahindra dynamic discount scheme: 0.5% for payment by Day 20 (vs Day 30 standard). Net benefit: ₹22,500. Working capital cost at 9% p.a. for 10 days: ₹11,137. Net gain: ₹11,363.", "applied": False, "applied_at": None, "status": "RECOMMENDED"},
    {"id": "AI006", "agent": "InvoiceCodingAgent", "invoice_id": "INV002", "type": "GL_CODING", "confidence": 88.5, "recommendation": "GL Account: 6600-001 (Administration — Office Supplies)", "reasoning": "Vendor category Office Supplies + HSN 4820 (Paper & stationery) + cost center CC-ADMIN-01", "applied": True, "applied_at": ts(6), "status": "APPLIED"},
    {"id": "AI007", "agent": "RiskAgent", "invoice_id": None, "supplier_id": "SUP009", "type": "SUPPLIER_RISK", "confidence": 72.1, "recommendation": "Suresh Traders: GSTR-1 non-filing for Aug 2024 — ITC risk", "reasoning": "Supplier has not filed GSTR-1 for Aug 2024 as of Sep 29. If pattern continues, ITC of ₹X may need reversal in upcoming reconciliation. Recommend payment hold pending GSTR-1 filing.", "applied": False, "applied_at": None, "status": "PENDING_ACTION"},
]

VENDOR_PORTAL_EVENTS = [
    {"id": "VPE001", "event_type": "vendor.onboarded", "timestamp": ts(10), "supplier_id": "SUP011", "supplier_name": "Karnataka Tech MSME Solutions", "payload": {"gstin": "29AABCK5432K1ZW", "category": "IT Services", "is_msme": True, "msme_category": "SMALL"}, "processed": True, "p2p_action": "Supplier record created in P2P Supplier Service"},
    {"id": "VPE002", "event_type": "vendor.bank_verified", "timestamp": ts(8), "supplier_id": "SUP011", "supplier_name": "Karnataka Tech MSME Solutions", "payload": {"bank_name": "Canara Bank", "ifsc": "CNRB0001234", "verification_source": "Penny Drop"}, "processed": True, "p2p_action": "Payment enabled for supplier in Payment Engine"},
    {"id": "VPE003", "event_type": "vendor.gstin_updated", "timestamp": ts(4), "supplier_id": "SUP005", "supplier_name": "Gujarat Tech Solutions", "payload": {"old_gstin": "24AATCG9876C1ZM", "new_gstin": "24AATCG9876C1ZM", "reason": "Address update — same GSTIN"}, "processed": True, "p2p_action": "GST cache refresh triggered for GSTIN 24AATCG9876C1ZM"},
    {"id": "VPE004", "event_type": "vendor.onboarded", "timestamp": ts(2), "supplier_id": "SUP012", "supplier_name": "Delhi Stationery Hub", "payload": {"gstin": "07AABCD6789M1ZY", "category": "Office Supplies", "is_msme": True, "msme_category": "MICRO"}, "processed": True, "p2p_action": "Supplier record created — pending bank verification"},
    {"id": "VPE005", "event_type": "vendor.document_expired", "timestamp": ts(1), "supplier_id": "SUP007", "supplier_name": "Mumbai Print House", "payload": {"document": "Trade License", "expiry_date": past(5), "renewal_submitted": False}, "processed": True, "p2p_action": "Risk score updated to 4.1. Notification sent to vendor portal team."},
    {"id": "VPE006", "event_type": "vendor.bank_verified", "timestamp": ts(0), "supplier_id": "SUP012", "supplier_name": "Delhi Stationery Hub", "payload": {"bank_name": "Indian Bank", "ifsc": "IDIB0001234", "verification_source": "Penny Drop", "status": "PENDING"}, "processed": False, "p2p_action": "Awaiting penny drop confirmation — payment not yet enabled"},
]


# ── Mutable state for demo interactions (legacy modules only) ────
_state = {
    "invoices": copy.deepcopy(INVOICES),
    "gst_cache": copy.deepcopy(GST_CACHE),
    "ebs_events": copy.deepcopy(EBS_EVENTS),
    "ai_insights": copy.deepcopy(AI_INSIGHTS),
    "vendor_events": copy.deepcopy(VENDOR_PORTAL_EVENTS),
    "suppliers": copy.deepcopy(SUPPLIERS),
    "gst_last_full_sync": ts(4, 15),
}


def fmt_inr(amount):
    if amount is None:
        return None
    if amount >= 10000000:
        return f"₹{amount/10000000:.1f}Cr"
    elif amount >= 100000:
        return f"₹{amount/100000:.1f}L"
    else:
        return f"₹{amount:,.0f}"


def get_supplier(sid):
    return next((s for s in _state["suppliers"] if s["id"] == sid), None)


def get_invoice(iid):
    return next((i for i in _state["invoices"] if i["id"] == iid), None)


# ─────────────────────────────────────────────
# APP FACTORY
# ─────────────────────────────────────────────

import logging
_logger = logging.getLogger("p2p.events")


async def _log_pr_event(event: Event) -> None:
    """Log PR lifecycle events for audit trail."""
    _logger.info("EVENT %s: %s", event.name, event.data)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler — startup/shutdown."""
    if settings.DATABASE_URL.startswith("sqlite"):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # Register event bus handlers
    event_bus.subscribe("pr.created", _log_pr_event)
    event_bus.subscribe("pr.approved", _log_pr_event)
    event_bus.subscribe("pr.rejected", _log_pr_event)

    yield


app = FastAPI(
    title="IDFC P2P Platform API",
    version="0.3.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENABLE_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_DOCS else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

# ── Mount DB-backed module routers ────────────────────────────────
app.include_router(auth_router)
app.include_router(suppliers_router)
app.include_router(budgets_router)
app.include_router(pr_router)
app.include_router(po_router)


# ─────────────────────────────────────────────
# LEGACY ENDPOINTS (in-memory, will be migrated)
# ─────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {
        "status": "ok", "version": "0.3.0",
        "services": {
            "supplier_service": "UP", "pr_po_service": "UP",
            "invoice_service": "UP", "gst_sync_service": "UP",
            "matching_engine": "UP", "workflow_engine": "UP",
            "payment_engine": "UP", "ebs_adapter": "UP",
            "ai_orchestrator": "UP",
        },
        "integrations": {
            "oracle_ebs": "CONNECTED (AP, GL, FA)",
            "cygnet_gsp": "CONNECTED (cache mode)",
            "vendor_portal": "CONNECTED (event stream)",
            "budget_module": "CONNECTED",
        }
    }


# ── Dashboard (hybrid — DB for migrated modules, in-memory for rest) ──

@app.get("/api/dashboard")
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    # In-memory data (not yet migrated)
    invoices = _state["invoices"]
    pending_invoices = [i for i in invoices if i["status"] in ("MATCHED", "PENDING_APPROVAL")]
    msme_at_risk = [i for i in invoices if i.get("msme_status") == "AT_RISK"]
    msme_breached = [i for i in invoices if i.get("msme_status") == "BREACHED"]
    ebs_failed = [e for e in _state["ebs_events"] if e["status"] == "FAILED"]
    fraud_blocked = [i for i in invoices if i.get("fraud_flag")]
    gst_issues = [g for g in _state["gst_cache"] if not g.get("gstr2b_available") or g.get("gstr1_compliance") == "DELAYED"]
    mtd_spend = sum(i["net_payable"] for i in invoices if i["status"] in ("APPROVED", "POSTED_TO_EBS", "PAID"))

    # DB queries for migrated modules
    pending_prs_result = await db.execute(
        select(func.count()).select_from(PurchaseRequest).where(PurchaseRequest.status == "PENDING_APPROVAL")
    )
    prs_pending = pending_prs_result.scalar() or 0

    active_pos_result = await db.execute(
        select(func.count()).select_from(PurchaseOrder).where(PurchaseOrder.status != "CLOSED")
    )
    active_pos = active_pos_result.scalar() or 0

    active_suppliers_result = await db.execute(
        select(func.count()).select_from(Supplier).where(Supplier.status == "ACTIVE")
    )
    active_suppliers = active_suppliers_result.scalar() or 0

    budgets_result = await db.execute(select(Budget).order_by(Budget.department_code))
    budgets = list(budgets_result.scalars().all())

    monthly_trend = [
        {"month": "Apr", "spend": 14200000}, {"month": "May", "spend": 18900000},
        {"month": "Jun", "spend": 12400000}, {"month": "Jul", "spend": 22100000},
        {"month": "Aug", "spend": 19800000}, {"month": "Sep", "spend": mtd_spend},
    ]
    spend_by_category = [
        {"category": "IT Services", "amount": 28500000, "pct": 38},
        {"category": "Consulting", "amount": 19200000, "pct": 26},
        {"category": "Facilities Mgmt", "amount": 12800000, "pct": 17},
        {"category": "Office Supplies", "amount": 6400000, "pct": 9},
        {"category": "Printing & Mktg", "amount": 5100000, "pct": 7},
        {"category": "Others", "amount": 2200000, "pct": 3},
    ]
    alerts = []
    if msme_breached:
        alerts.append({"type": "CRITICAL", "icon": "alert", "msg": f"{len(msme_breached)} MSME invoice(s) in breach — Sec 43B(h) penalty accruing", "link": "/msme"})
    if msme_at_risk:
        alerts.append({"type": "WARNING", "icon": "clock", "msg": f"{len(msme_at_risk)} MSME invoice(s) at risk — payment due within 7 days", "link": "/msme"})
    if ebs_failed:
        alerts.append({"type": "ERROR", "icon": "server", "msg": f"{len(ebs_failed)} Oracle EBS posting(s) failed — manual retry required", "link": "/ebs"})
    if fraud_blocked:
        alerts.append({"type": "WARNING", "icon": "shield", "msg": f"{len(fraud_blocked)} invoice(s) auto-rejected by Fraud Detection Agent", "link": "/invoices"})
    if gst_issues:
        alerts.append({"type": "INFO", "icon": "database", "msg": f"{len(gst_issues)} supplier GST record(s) need attention (missing GSTR-2B / non-filing)", "link": "/gst-cache"})
    activity = [
        {"time": ts(0), "icon": "upload", "color": "blue", "msg": "Invoice SOD/2024/INV/3421 uploaded by Deepak Nair"},
        {"time": ts(1), "icon": "check", "color": "green", "msg": "Invoice TM/2024/8821 posted to Oracle AP — Ref: EBS-AP-78234"},
        {"time": ts(2), "icon": "shield", "color": "red", "msg": "Fraud agent auto-rejected INV003 (duplicate of INV001)"},
        {"time": ts(3), "icon": "alert", "color": "orange", "msg": "MSME breach: Mumbai Print House — ₹8,428 penalty accruing"},
        {"time": ts(4), "icon": "refresh", "color": "blue", "msg": "Vendor portal sync: Karnataka Tech MSME bank verified"},
        {"time": ts(5), "icon": "clock", "color": "yellow", "msg": "SLA Agent: Gujarat Tech Solutions MSME — 7 days remaining"},
    ]
    return {
        "stats": {
            "invoices_pending": len(pending_invoices),
            "mtd_spend": mtd_spend, "mtd_spend_fmt": fmt_inr(mtd_spend),
            "active_pos": active_pos,
            "active_suppliers": active_suppliers,
            "prs_pending": prs_pending,
            "msme_at_risk_count": len(msme_at_risk) + len(msme_breached),
            "ebs_failures": len(ebs_failed), "fraud_blocked": len(fraud_blocked),
            "gst_cache_age_hours": 4.2, "gst_last_sync": _state["gst_last_full_sync"],
        },
        "alerts": alerts, "monthly_trend": monthly_trend,
        "spend_by_category": spend_by_category, "activity": activity,
        "budget_utilization": [
            {"dept": b.department_name, "total": b.total_amount,
             "committed": b.committed_amount, "actual": b.actual_amount,
             "available": b.available_amount,
             "utilization_pct": round((b.committed_amount + b.actual_amount) / b.total_amount * 100, 1) if b.total_amount else 0}
            for b in budgets
        ]
    }


# ── Invoices (legacy) ─────────────────────────────────────────────

@app.get("/api/invoices")
def get_invoices(status: str = None):
    invs = _state["invoices"]
    if status:
        invs = [i for i in invs if i["status"] == status]
    return invs

@app.get("/api/invoices/{inv_id}")
async def get_invoice_detail(inv_id: str, db: AsyncSession = Depends(get_db)):
    inv = get_invoice(inv_id)
    if not inv:
        raise HTTPException(404)
    supplier = get_supplier(inv["supplier_id"])
    gst_data = next((g for g in _state["gst_cache"] if g.get("gstin") == inv.get("gstin_supplier")), None)
    # POs and GRNs are now in DB — query by po_number/grn_number
    po_dict = None
    grn_dict = None
    if inv.get("po_id"):
        po_result = await db.execute(
            select(PurchaseOrder).where(PurchaseOrder.po_number == inv["po_id"])
        )
        po_row = po_result.scalar_one_or_none()
        if po_row:
            po_dict = {k: v for k, v in po_row.__dict__.items() if not k.startswith("_")}
            po_dict["id"] = po_row.po_number
    if inv.get("grn_id"):
        from backend.modules.purchase_orders.models import GoodsReceiptNote
        grn_result = await db.execute(
            select(GoodsReceiptNote).where(GoodsReceiptNote.grn_number == inv["grn_id"])
        )
        grn_row = grn_result.scalar_one_or_none()
        if grn_row:
            grn_dict = {k: v for k, v in grn_row.__dict__.items() if not k.startswith("_")}
            grn_dict["id"] = grn_row.grn_number
    ai_results = [a for a in _state["ai_insights"] if a.get("invoice_id") == inv_id]
    ebs_events = [e for e in _state["ebs_events"] if e["entity_id"] == inv_id]
    return {
        **inv, "supplier": supplier, "gst_cache_data": gst_data,
        "purchase_order": po_dict, "grn": grn_dict,
        "ai_insights": ai_results, "ebs_events": ebs_events,
    }

@app.patch("/api/invoices/{inv_id}/approve")
def approve_invoice(inv_id: str):
    inv = get_invoice(inv_id)
    if not inv:
        raise HTTPException(404)
    allowed = ("MATCHED", "PENDING_APPROVAL", "VALIDATED")
    if inv["status"] not in allowed:
        raise HTTPException(400, f"Cannot approve invoice in status {inv['status']}")
    inv["status"] = "APPROVED"
    inv["approved_by"] = "Demo Approver"
    inv["approved_at"] = ts(0)
    inv["ebs_ap_status"] = "PENDING"
    ebs_id = f"EBS{len(_state['ebs_events']) + 1:03d}"
    _state["ebs_events"].append({
        "id": ebs_id, "event_type": "INVOICE_POST", "entity_id": inv_id,
        "entity_ref": inv["invoice_number"],
        "description": "Invoice → AP Open Interface (Approved)",
        "gl_account": inv.get("coding_agent_gl", "TBD"),
        "amount": inv["net_payable"], "ebs_module": "AP", "status": "PENDING",
        "sent_at": ts(0), "acknowledged_at": None, "ebs_ref": None, "error_message": None
    })
    return inv

@app.patch("/api/invoices/{inv_id}/reject")
def reject_invoice(inv_id: str, reason: str = "Rejected via demo"):
    inv = get_invoice(inv_id)
    if not inv:
        raise HTTPException(404)
    inv["status"] = "REJECTED"
    inv["rejected_at"] = ts(0)
    inv["rejection_reason"] = reason
    return inv

@app.post("/api/invoices/{inv_id}/simulate-processing")
def simulate_ocr_and_validation(inv_id: str):
    inv = get_invoice(inv_id)
    if not inv:
        raise HTTPException(404)
    if inv["status"] == "CAPTURED":
        inv["status"] = "EXTRACTED"
        inv["ocr_confidence"] = round(random.uniform(85, 99), 1)
    elif inv["status"] == "EXTRACTED":
        inv["status"] = "VALIDATED"
        inv["gstin_validated_from_cache"] = True
        inv["gstin_cache_status"] = "ACTIVE"
        inv["gstin_cache_age_hours"] = round(random.uniform(1, 8), 1)
    elif inv["status"] == "VALIDATED":
        inv["status"] = "MATCHED"
        inv["match_status"] = "2WAY_MATCH_PASSED"
        inv["coding_agent_gl"] = "6600-002"
        inv["coding_agent_confidence"] = round(random.uniform(80, 95), 1)
        inv["coding_agent_category"] = "Facilities Management"
    elif inv["status"] == "MATCHED":
        inv["status"] = "PENDING_APPROVAL"
    return inv


# ── GST Cache (legacy) ────────────────────────────────────────────

@app.get("/api/gst-cache")
def get_gst_cache():
    return {
        "records": _state["gst_cache"],
        "last_full_sync": _state["gst_last_full_sync"],
        "total": len(_state["gst_cache"]),
        "active": len([g for g in _state["gst_cache"] if g["status"] == "ACTIVE"]),
        "gstr2b_available": len([g for g in _state["gst_cache"] if g.get("gstr2b_available")]),
        "gstr2b_missing": len([g for g in _state["gst_cache"] if not g.get("gstr2b_available")]),
        "gstr1_delayed": len([g for g in _state["gst_cache"] if g.get("gstr1_compliance") == "DELAYED"]),
        "total_cache_hits": sum(g.get("cache_hit_count", 0) for g in _state["gst_cache"]),
        "live_calls_avoided": sum(g.get("cache_hit_count", 0) for g in _state["gst_cache"]),
        "sync_provider": "Cygnet GSP",
    }

@app.post("/api/gst-cache/sync")
def trigger_gst_sync():
    now = ts(0)
    _state["gst_last_full_sync"] = now
    updated = 0
    for record in _state["gst_cache"]:
        record["last_synced"] = now
        record["sync_source"] = "CYGNET_BATCH"
        if not record.get("gstr2b_available") and random.random() > 0.5:
            record["gstr2b_available"] = True
            record["gstr2b_period"] = "Aug 2024"
            record.pop("gstr2b_alert", None)
            updated += 1
    return {
        "status": "SYNC_COMPLETE", "synced_at": now, "provider": "Cygnet GSP",
        "records_updated": updated, "total_gstins": len(_state["gst_cache"]),
        "batch_type": "INCREMENTAL",
        "note": "GSTR-2B and GSTIN status refreshed. IRN rules unchanged."
    }


# ── MSME Compliance (legacy) ──────────────────────────────────────

@app.get("/api/msme-compliance")
def get_msme_compliance():
    msme_invoices = [i for i in _state["invoices"] if i.get("is_msme_supplier")]
    summary = {
        "total_msme_invoices": len(msme_invoices),
        "on_track": len([i for i in msme_invoices if i.get("msme_status") == "ON_TRACK"]),
        "at_risk": len([i for i in msme_invoices if i.get("msme_status") == "AT_RISK"]),
        "breached": len([i for i in msme_invoices if i.get("msme_status") == "BREACHED"]),
        "total_pending_msme_amount": sum(i["net_payable"] for i in msme_invoices if i["status"] not in ("PAID", "REJECTED")),
        "total_penalty_accrued": sum(i.get("msme_penalty_amount", 0) for i in msme_invoices),
        "section_43bh": "Section 43B(h) — Finance Act 2023 (effective Apr 1, 2024)",
        "max_payment_days": 45, "rbi_rate": 6.5, "penalty_multiplier": 3,
    }
    detailed = []
    for i in msme_invoices:
        detailed.append({
            "invoice_id": i["id"], "invoice_number": i["invoice_number"],
            "supplier_name": i["supplier_name"], "msme_category": i.get("msme_category"),
            "invoice_date": i["invoice_date"], "invoice_amount": i["net_payable"],
            "invoice_status": i["status"], "msme_due_date": i.get("msme_due_date"),
            "days_remaining": i.get("msme_days_remaining"), "msme_status": i.get("msme_status"),
            "penalty_amount": i.get("msme_penalty_amount"),
            "risk_level": "RED" if i.get("msme_status") == "BREACHED" else
                          "AMBER" if i.get("msme_status") == "AT_RISK" else "GREEN",
        })
    return {"summary": summary, "invoices": detailed}


# ── Oracle EBS (legacy) ───────────────────────────────────────────

@app.get("/api/oracle-ebs/events")
def get_ebs_events():
    return {
        "events": _state["ebs_events"],
        "summary": {
            "total": len(_state["ebs_events"]),
            "acknowledged": len([e for e in _state["ebs_events"] if e["status"] == "ACKNOWLEDGED"]),
            "pending": len([e for e in _state["ebs_events"] if e["status"] == "PENDING"]),
            "failed": len([e for e in _state["ebs_events"] if e["status"] == "FAILED"]),
        },
        "ebs_modules_active": ["AP", "GL", "FA"],
        "ebs_modules_retired": ["PR", "PO", "Invoice UI"],
        "integration_method": "Oracle Integration Cloud (OIC) → EBS ISG",
    }

@app.post("/api/oracle-ebs/events/{event_id}/retry")
def retry_ebs_event(event_id: str):
    event = next((e for e in _state["ebs_events"] if e["id"] == event_id), None)
    if not event:
        raise HTTPException(404)
    if event["status"] != "FAILED":
        raise HTTPException(400, "Only FAILED events can be retried")
    event["status"] = "ACKNOWLEDGED"
    event["acknowledged_at"] = ts(0)
    event["ebs_ref"] = f"EBS-AP-{random.randint(78000, 79999)}"
    event["error_message"] = None
    if event["entity_id"]:
        inv = get_invoice(event["entity_id"])
        if inv:
            inv["ebs_ap_status"] = "POSTED"
            inv["ebs_ap_ref"] = event["ebs_ref"]
            inv["ebs_posted_at"] = ts(0)
            if inv["status"] == "APPROVED":
                inv["status"] = "POSTED_TO_EBS"
    return {"status": "retried", "event": event}


# ── AI Agents (legacy) ────────────────────────────────────────────

@app.get("/api/ai-agents/insights")
def get_ai_insights():
    return {
        "insights": _state["ai_insights"],
        "agents": [
            {"name": "InvoiceCodingAgent", "status": "ACTIVE", "model": "fine-tuned-bert-v2.1", "avg_confidence": 91.2, "invoices_coded_mtd": 23, "accuracy_feedback": 94.5},
            {"name": "FraudDetectionAgent", "status": "ACTIVE", "model": "isolation-forest-v3.0", "avg_confidence": 96.8, "flags_raised_mtd": 2, "false_positive_rate": 0.8},
            {"name": "SLAPredictionAgent", "status": "ACTIVE", "model": "gradient-boost-v1.4", "avg_confidence": 94.1, "alerts_raised_mtd": 4, "breach_prevention_rate": 87.5},
            {"name": "CashOptimizationAgent", "status": "ACTIVE", "model": "reinforcement-learning-v1.2", "avg_confidence": 76.4, "recommendations_mtd": 8, "savings_identified": 87500},
            {"name": "RiskAgent", "status": "ACTIVE", "model": "xgboost-supplier-v2.0", "avg_confidence": 81.3, "suppliers_scored": 15, "high_risk_flagged": 3},
        ]
    }

@app.post("/api/ai-agents/insights/{insight_id}/apply")
def apply_ai_insight(insight_id: str):
    insight = next((a for a in _state["ai_insights"] if a["id"] == insight_id), None)
    if not insight:
        raise HTTPException(404)
    insight["applied"] = True
    insight["applied_at"] = ts(0)
    insight["status"] = "APPLIED"
    return insight


# ── Vendor Portal Events (legacy) ─────────────────────────────────

@app.get("/api/vendor-portal/events")
def get_vendor_events():
    return _state["vendor_events"]


# ── Spend Analytics (legacy) ──────────────────────────────────────

@app.get("/api/analytics/spend")
def get_spend_analytics():
    return {
        "spend_by_category": [
            {"category": "IT Services", "amount": 28500000, "invoices": 45, "vendors": 5},
            {"category": "Consulting", "amount": 19200000, "invoices": 28, "vendors": 3},
            {"category": "Facilities Mgmt", "amount": 12800000, "invoices": 36, "vendors": 4},
            {"category": "Office Supplies", "amount": 6400000, "invoices": 62, "vendors": 5},
            {"category": "Printing & Mktg", "amount": 5100000, "invoices": 18, "vendors": 2},
            {"category": "Others", "amount": 2200000, "invoices": 12, "vendors": 2},
        ],
        "monthly_trend": [
            {"month": "Apr 24", "it": 5200000, "consulting": 3100000, "facilities": 2400000, "other": 3500000},
            {"month": "May 24", "it": 6800000, "consulting": 4200000, "facilities": 2200000, "other": 5700000},
            {"month": "Jun 24", "it": 4100000, "consulting": 2800000, "facilities": 2100000, "other": 3400000},
            {"month": "Jul 24", "it": 8200000, "consulting": 5100000, "facilities": 3100000, "other": 5700000},
            {"month": "Aug 24", "it": 7400000, "consulting": 4600000, "facilities": 2800000, "other": 5000000},
            {"month": "Sep 24", "it": 4500000, "consulting": 1800000, "facilities": 0, "other": 0},
        ],
        "top_vendors": [
            {"name": "TechMahindra Solutions", "amount": 12400000, "invoices": 18, "on_time_pct": 98},
            {"name": "Deloitte Advisory LLP", "amount": 9800000, "invoices": 12, "on_time_pct": 100},
            {"name": "KPMG India Pvt Ltd", "amount": 8400000, "invoices": 10, "on_time_pct": 95},
            {"name": "Infosys BPM Ltd", "amount": 7200000, "invoices": 14, "on_time_pct": 97},
            {"name": "Sodexo Facilities India", "amount": 6800000, "invoices": 24, "on_time_pct": 99},
        ],
        "budget_vs_actual": [
            {"dept": "Technology", "budget": 80000000, "committed": 22000000, "actual": 30000000},
            {"dept": "Operations", "budget": 40000000, "committed": 8000000, "actual": 12000000},
            {"dept": "Finance", "budget": 30000000, "committed": 5000000, "actual": 10500000},
            {"dept": "Marketing", "budget": 20000000, "committed": 4000000, "actual": 8000000},
            {"dept": "HR", "budget": 10000000, "committed": 1500000, "actual": 2500000},
            {"dept": "Admin", "budget": 15000000, "committed": 3000000, "actual": 8000000},
        ],
        "kpis": {
            "invoice_cycle_time_days": 4.2, "three_way_match_rate_pct": 81.4,
            "auto_approval_rate_pct": 34.2, "early_payment_savings_mtd": 87500,
            "maverick_spend_pct": 6.3, "po_coverage_pct": 73.8,
        }
    }


# ─────────────────────────────────────────────
# SERVE FRONTEND (SPA)
# ─────────────────────────────────────────────

_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(_dist, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        return FileResponse(os.path.join(_dist, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
