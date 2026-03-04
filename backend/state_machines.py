"""
State Machine Definitions — Allowed Status Transitions

Prevents invalid status jumps (e.g., DRAFT → PAID).
Each entity type defines a map of current_status → [allowed_next_statuses].
"""

from __future__ import annotations

from backend.exceptions import ValidationError


# ---------------------------------------------------------------------------
# Invoice lifecycle
# ---------------------------------------------------------------------------

INVOICE_TRANSITIONS: dict[str, list[str]] = {
    "CAPTURED": ["EXTRACTED", "REJECTED"],
    "EXTRACTED": ["VALIDATED", "REJECTED"],
    "VALIDATED": ["MATCHED", "REJECTED"],
    "MATCHED": ["PENDING_APPROVAL", "REJECTED"],
    "PENDING_APPROVAL": ["APPROVED", "REJECTED"],
    "APPROVED": ["POSTED_TO_EBS", "REJECTED"],
    "POSTED_TO_EBS": ["PAID"],
    "PAID": [],  # terminal
    "REJECTED": [],  # terminal
}

# ---------------------------------------------------------------------------
# Purchase Request lifecycle
# ---------------------------------------------------------------------------

PR_TRANSITIONS: dict[str, list[str]] = {
    "DRAFT": ["PENDING_APPROVAL"],
    "PENDING_APPROVAL": ["APPROVED", "REJECTED"],
    "APPROVED": [],  # terminal — PO gets created
    "REJECTED": [],  # terminal
}

# ---------------------------------------------------------------------------
# Purchase Order lifecycle
# ---------------------------------------------------------------------------

PO_TRANSITIONS: dict[str, list[str]] = {
    "DRAFT": ["ISSUED"],
    "ISSUED": ["ACKNOWLEDGED", "PARTIALLY_RECEIVED", "RECEIVED", "CLOSED"],
    "ACKNOWLEDGED": ["PARTIALLY_RECEIVED", "RECEIVED", "CLOSED"],
    "PARTIALLY_RECEIVED": ["RECEIVED", "CLOSED"],
    "RECEIVED": ["CLOSED"],
    "CLOSED": [],  # terminal
}

# ---------------------------------------------------------------------------
# Payment Run lifecycle
# ---------------------------------------------------------------------------

PAYMENT_RUN_TRANSITIONS: dict[str, list[str]] = {
    "DRAFT": ["SCHEDULED", "CANCELLED"],
    "SCHEDULED": ["PROCESSING", "CANCELLED"],
    "PROCESSING": ["COMPLETED", "FAILED"],
    "COMPLETED": [],  # terminal
    "FAILED": ["SCHEDULED"],  # can retry
    "CANCELLED": [],  # terminal
}

# ---------------------------------------------------------------------------
# Payment lifecycle
# ---------------------------------------------------------------------------

PAYMENT_TRANSITIONS: dict[str, list[str]] = {
    "PENDING": ["SCHEDULED"],
    "SCHEDULED": ["PROCESSING"],
    "PROCESSING": ["COMPLETED", "FAILED"],
    "COMPLETED": ["REVERSED"],
    "FAILED": ["PENDING"],  # can retry
    "REVERSED": [],  # terminal
}

# ---------------------------------------------------------------------------
# Contract lifecycle
# ---------------------------------------------------------------------------

CONTRACT_TRANSITIONS: dict[str, list[str]] = {
    "DRAFT": ["ACTIVE"],
    "ACTIVE": ["EXPIRED", "TERMINATED", "RENEWED"],
    "EXPIRED": ["RENEWED"],
    "TERMINATED": [],  # terminal
    "RENEWED": ["ACTIVE", "EXPIRED", "TERMINATED"],
}

# ---------------------------------------------------------------------------
# RFQ lifecycle
# ---------------------------------------------------------------------------

RFQ_TRANSITIONS: dict[str, list[str]] = {
    "DRAFT": ["PUBLISHED", "CANCELLED"],
    "PUBLISHED": ["EVALUATION", "CANCELLED"],
    "EVALUATION": ["AWARDED", "CANCELLED"],
    "AWARDED": [],  # terminal
    "CANCELLED": [],  # terminal
}


# ---------------------------------------------------------------------------
# Validation helper
# ---------------------------------------------------------------------------

def validate_maker_checker(
    maker: str | None,
    checker: str | None,
    entity_type: str = "entity",
) -> None:
    """Enforce maker-checker: the approver must differ from the creator.

    Both values are typically user IDs or names. If either is None/empty,
    the check is skipped (backwards-compatible with dev mode).
    """
    if not maker or not checker:
        return

    if maker.strip().lower() == checker.strip().lower():
        raise ValidationError(
            f"Maker-checker violation on {entity_type}: "
            f"the same user ({checker}) cannot both create and approve."
        )


def validate_transition(
    entity_type: str,
    current_status: str,
    new_status: str,
) -> None:
    """Raise ValidationError if the transition is not allowed."""
    machines = {
        "invoice": INVOICE_TRANSITIONS,
        "purchase_request": PR_TRANSITIONS,
        "purchase_order": PO_TRANSITIONS,
        "payment_run": PAYMENT_RUN_TRANSITIONS,
        "payment": PAYMENT_TRANSITIONS,
        "contract": CONTRACT_TRANSITIONS,
        "rfq": RFQ_TRANSITIONS,
    }

    transitions = machines.get(entity_type)
    if transitions is None:
        return  # no state machine defined for this entity

    allowed = transitions.get(current_status, [])
    if new_status not in allowed:
        raise ValidationError(
            f"Invalid {entity_type} transition: {current_status} → {new_status}. "
            f"Allowed: {allowed or ['(terminal state)']}"
        )
