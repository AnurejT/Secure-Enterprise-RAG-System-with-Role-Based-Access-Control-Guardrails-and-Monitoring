"""
backend/rbac/policies.py
RBAC policy definitions — role hierarchy and permission sets.
"""

# Role hierarchy (higher index = more privilege)
ROLE_HIERARCHY = ["guest", "general", "finance", "hr", "marketing", "engineering", "admin"]

# Departments that have dedicated document namespaces
DEPARTMENT_ROLES = {"finance", "hr", "marketing", "engineering"}

# Roles with admin-level access
ADMIN_ROLES = {"admin"}


def get_role_level(role: str) -> int:
    """Return the privilege level for a given role (higher = more access)."""
    try:
        return ROLE_HIERARCHY.index(role.lower())
    except ValueError:
        return 0


def can_access_department(user_role: str, department: str) -> bool:
    """Check if a user role may access a specific department's documents."""
    if user_role == "admin":
        return True
    if department == "general":
        return user_role != "guest"
    return user_role == department
