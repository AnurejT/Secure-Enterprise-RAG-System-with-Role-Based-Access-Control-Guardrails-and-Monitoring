"""
backend/rbac/enforcement.py
RBAC filtering — determines which documents a given role may read.
Extracted from rag/retriever.py so it's independently testable.
"""


ADMIN_ROLE = "admin"
GENERAL_ROLE = "general"


def is_document_allowed(doc, user_role: str) -> bool:
    """
    Return True if `user_role` is permitted to read `doc`.

    Rules:
    - admin  → sees everything
    - general → accessible by all authenticated (non-guest) users
    - otherwise → user_role must appear explicitly in doc's role_allowed list
    """
    roles = doc.metadata.get("role_allowed", [])

    # Normalise: stored as comma-string or list
    if isinstance(roles, str):
        roles = [r.strip() for r in roles.split(",")]
    roles = [r.lower() for r in roles]

    user_role = user_role.lower()

    if user_role == ADMIN_ROLE:
        return True
    if user_role in roles:
        return True
    if GENERAL_ROLE in roles and user_role != "guest":
        return True
    return False


def filter_by_role(docs: list, user_role: str) -> list:
    """Filter a list of documents to only those the user may access."""
    allowed = [d for d in docs if is_document_allowed(d, user_role)]
    print(f"[RBAC] {len(docs)} docs -> {len(allowed)} allowed for role='{user_role}'")
    return allowed
