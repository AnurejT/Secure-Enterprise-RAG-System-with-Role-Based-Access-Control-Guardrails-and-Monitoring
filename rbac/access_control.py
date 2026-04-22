# rbac/access_control.py

def is_allowed(user_role, doc_roles):
    return user_role.lower() in doc_roles or "admin" in doc_roles