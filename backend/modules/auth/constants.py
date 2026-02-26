"""
Auth Module — Constants

Role definitions and hierarchy for the P2P platform.
Higher numeric level = more privileges.
"""

# ---------------------------------------------------------------------------
# Role identifiers
# ---------------------------------------------------------------------------

ADMIN = "ADMIN"
FINANCE_HEAD = "FINANCE_HEAD"
PROCUREMENT_MANAGER = "PROCUREMENT_MANAGER"
DEPARTMENT_HEAD = "DEPARTMENT_HEAD"
VIEWER = "VIEWER"

ALL_ROLES: list[str] = [
    ADMIN,
    FINANCE_HEAD,
    PROCUREMENT_MANAGER,
    DEPARTMENT_HEAD,
    VIEWER,
]

# ---------------------------------------------------------------------------
# Role hierarchy — higher level = more authority
# ---------------------------------------------------------------------------

ROLE_HIERARCHY: dict[str, int] = {
    VIEWER: 10,
    DEPARTMENT_HEAD: 20,
    PROCUREMENT_MANAGER: 30,
    FINANCE_HEAD: 40,
    ADMIN: 50,
}


def has_minimum_role(user_role: str, required_role: str) -> bool:
    """Return True if *user_role* is at or above *required_role* in the hierarchy."""
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    required_level = ROLE_HIERARCHY.get(required_role, 0)
    return user_level >= required_level
