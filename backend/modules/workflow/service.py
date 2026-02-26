"""
Workflow Module — Service Layer

Business logic for approval workflows: creating approval requests,
evaluating matrices, approving/rejecting steps, and escalation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.event_bus import Event, event_bus
from backend.modules.workflow.models import ApprovalMatrix, ApprovalInstance, ApprovalStep


# ---------------------------------------------------------------------------
# Approval Matrix CRUD
# ---------------------------------------------------------------------------

async def list_matrices(db: AsyncSession) -> List[Dict[str, Any]]:
    """Return all approval matrix rules."""
    result = await db.execute(
        select(ApprovalMatrix).order_by(ApprovalMatrix.entity_type, ApprovalMatrix.level)
    )
    rows = result.scalars().all()
    return [_matrix_to_dict(m) for m in rows]


async def create_matrix(db: AsyncSession, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new approval matrix rule."""
    matrix = ApprovalMatrix(**data)
    db.add(matrix)
    await db.commit()
    await db.refresh(matrix)
    return _matrix_to_dict(matrix)


async def get_matching_rules(
    db: AsyncSession,
    entity_type: str,
    department: Optional[str] = None,
    amount: float = 0,
) -> List[ApprovalMatrix]:
    """Find applicable approval rules for an entity."""
    q = select(ApprovalMatrix).where(
        ApprovalMatrix.entity_type == entity_type,
        ApprovalMatrix.is_active == True,
        ApprovalMatrix.min_amount <= amount,
        ApprovalMatrix.max_amount >= amount,
    )
    if department:
        # Match rules that either target this department or have no dept filter
        q = q.where(
            (ApprovalMatrix.department == department)
            | (ApprovalMatrix.department == None)  # noqa: E711
        )
    q = q.order_by(ApprovalMatrix.level)
    result = await db.execute(q)
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Approval Instance Lifecycle
# ---------------------------------------------------------------------------

async def create_approval_request(
    db: AsyncSession,
    entity_type: str,
    entity_id: str,
    department: Optional[str] = None,
    amount: float = 0,
    requested_by: Optional[str] = None,
    entity_ref: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new approval instance with steps based on the matrix rules."""
    rules = await get_matching_rules(db, entity_type, department, amount)

    # Default to single-level approval if no rules match
    if not rules:
        rules_data = [{"level": 1, "approver_role": "FINANCE_HEAD"}]
    else:
        rules_data = [{"level": r.level, "approver_role": r.approver_role} for r in rules]

    total_levels = len(rules_data)

    instance = ApprovalInstance(
        entity_type=entity_type,
        entity_id=entity_id,
        entity_ref=entity_ref,
        department=department,
        amount=amount,
        total_levels=total_levels,
        current_level=1,
        status="PENDING",
        requested_by=requested_by,
    )
    db.add(instance)
    await db.flush()

    steps = []
    for rd in rules_data:
        step = ApprovalStep(
            instance_id=instance.id,
            level=rd["level"],
            approver_role=rd["approver_role"],
            status="PENDING" if rd["level"] == 1 else "PENDING",
        )
        db.add(step)
        steps.append(step)

    await db.commit()
    await db.refresh(instance)
    for s in steps:
        await db.refresh(s)

    await event_bus.publish(Event(
        name="workflow.approval_requested",
        data={"entity_type": entity_type, "entity_id": entity_id, "levels": total_levels},
        source="workflow",
    ))

    return _instance_to_dict(instance, steps)


async def list_pending_approvals(
    db: AsyncSession,
    approver_role: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List all pending approval instances, optionally filtered by approver role."""
    q = select(ApprovalInstance).where(ApprovalInstance.status == "PENDING")
    q = q.order_by(ApprovalInstance.created_at.desc())
    result = await db.execute(q)
    instances = result.scalars().all()

    out = []
    for inst in instances:
        steps = await _get_steps(db, inst.id)
        # Filter by role if specified
        if approver_role:
            current_step = next(
                (s for s in steps if s.level == inst.current_level), None
            )
            if current_step and current_step.approver_role != approver_role:
                continue
        out.append(_instance_to_dict(inst, steps))
    return out


async def get_approval_instance(
    db: AsyncSession,
    instance_id: str,
) -> Optional[Dict[str, Any]]:
    """Get a single approval instance with its steps."""
    result = await db.execute(
        select(ApprovalInstance).where(ApprovalInstance.id == instance_id)
    )
    inst = result.scalar_one_or_none()
    if not inst:
        return None
    steps = await _get_steps(db, inst.id)
    return _instance_to_dict(inst, steps)


async def get_approval_by_entity(
    db: AsyncSession,
    entity_type: str,
    entity_id: str,
) -> Optional[Dict[str, Any]]:
    """Get the latest approval instance for an entity."""
    result = await db.execute(
        select(ApprovalInstance)
        .where(
            ApprovalInstance.entity_type == entity_type,
            ApprovalInstance.entity_id == entity_id,
        )
        .order_by(ApprovalInstance.created_at.desc())
        .limit(1)
    )
    inst = result.scalar_one_or_none()
    if not inst:
        return None
    steps = await _get_steps(db, inst.id)
    return _instance_to_dict(inst, steps)


async def approve_step(
    db: AsyncSession,
    instance_id: str,
    approver_name: str,
    comments: Optional[str] = None,
) -> Dict[str, Any]:
    """Approve the current step and advance to next level or complete."""
    result = await db.execute(
        select(ApprovalInstance).where(ApprovalInstance.id == instance_id)
    )
    inst = result.scalar_one_or_none()
    if not inst:
        raise ValueError(f"Approval instance {instance_id} not found")
    if inst.status != "PENDING":
        raise ValueError(f"Instance is {inst.status}, not PENDING")

    steps = await _get_steps(db, inst.id)
    current_step = next((s for s in steps if s.level == inst.current_level), None)
    if not current_step:
        raise ValueError("No step found for current level")

    # Mark step as approved
    current_step.status = "APPROVED"
    current_step.approver_name = approver_name
    current_step.comments = comments
    current_step.acted_at = datetime.utcnow()

    # Check if all levels are done
    if inst.current_level >= inst.total_levels:
        inst.status = "APPROVED"
        inst.completed_at = datetime.utcnow()
        event_name = f"workflow.{inst.entity_type.lower()}_approved"
    else:
        inst.current_level += 1
        event_name = f"workflow.step_approved"

    await db.commit()
    await db.refresh(inst)
    steps = await _get_steps(db, inst.id)

    await event_bus.publish(Event(
        name=event_name,
        data={
            "entity_type": inst.entity_type,
            "entity_id": inst.entity_id,
            "level": current_step.level,
            "approver": approver_name,
            "status": inst.status,
        },
        source="workflow",
    ))

    return _instance_to_dict(inst, steps)


async def reject_step(
    db: AsyncSession,
    instance_id: str,
    approver_name: str,
    comments: Optional[str] = None,
) -> Dict[str, Any]:
    """Reject at the current step — entire approval is rejected."""
    result = await db.execute(
        select(ApprovalInstance).where(ApprovalInstance.id == instance_id)
    )
    inst = result.scalar_one_or_none()
    if not inst:
        raise ValueError(f"Approval instance {instance_id} not found")
    if inst.status != "PENDING":
        raise ValueError(f"Instance is {inst.status}, not PENDING")

    steps = await _get_steps(db, inst.id)
    current_step = next((s for s in steps if s.level == inst.current_level), None)
    if not current_step:
        raise ValueError("No step found for current level")

    current_step.status = "REJECTED"
    current_step.approver_name = approver_name
    current_step.comments = comments
    current_step.acted_at = datetime.utcnow()

    inst.status = "REJECTED"
    inst.completed_at = datetime.utcnow()

    # Skip remaining steps
    for step in steps:
        if step.level > inst.current_level and step.status == "PENDING":
            step.status = "SKIPPED"

    await db.commit()
    await db.refresh(inst)
    steps = await _get_steps(db, inst.id)

    await event_bus.publish(Event(
        name=f"workflow.{inst.entity_type.lower()}_rejected",
        data={
            "entity_type": inst.entity_type,
            "entity_id": inst.entity_id,
            "level": current_step.level,
            "approver": approver_name,
            "reason": comments,
        },
        source="workflow",
    ))

    return _instance_to_dict(inst, steps)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_steps(db: AsyncSession, instance_id: str) -> List[ApprovalStep]:
    result = await db.execute(
        select(ApprovalStep)
        .where(ApprovalStep.instance_id == instance_id)
        .order_by(ApprovalStep.level)
    )
    return list(result.scalars().all())


def _matrix_to_dict(m: ApprovalMatrix) -> Dict[str, Any]:
    return {
        "id": m.id,
        "entity_type": m.entity_type,
        "department": m.department,
        "category": m.category,
        "min_amount": m.min_amount,
        "max_amount": m.max_amount,
        "approver_role": m.approver_role,
        "level": m.level,
        "is_active": m.is_active,
    }


def _instance_to_dict(
    inst: ApprovalInstance,
    steps: List[ApprovalStep],
) -> Dict[str, Any]:
    return {
        "id": inst.id,
        "entity_type": inst.entity_type,
        "entity_id": inst.entity_id,
        "department": inst.department,
        "amount": inst.amount,
        "total_levels": inst.total_levels,
        "current_level": inst.current_level,
        "status": inst.status,
        "requested_by": inst.requested_by,
        "steps": [
            {
                "id": s.id,
                "level": s.level,
                "approver_role": s.approver_role,
                "approver_name": s.approver_name,
                "status": s.status,
                "comments": s.comments,
                "acted_at": s.acted_at.isoformat() if s.acted_at else None,
            }
            for s in steps
        ],
        "created_at": inst.created_at.isoformat() if inst.created_at else None,
        "completed_at": inst.completed_at.isoformat() if inst.completed_at else None,
    }
