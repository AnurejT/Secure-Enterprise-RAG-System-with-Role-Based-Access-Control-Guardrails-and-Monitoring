# rbac/access_control.py

def filter_docs_by_role(documents, user_role):
    user_role = user_role.lower()

    print(f"\n[RBAC] User Role: {user_role}")

    # Admin → full access
    if user_role == "admin":
        return documents

    filtered = []

    for doc in documents:
        roles = doc.metadata.get("role_allowed", [])
        dept = doc.metadata.get("department")

        # ✅ Allow if role matches
        if user_role in roles:
            filtered.append(doc)

        # 🔥 Backup: allow department match
        elif dept == user_role:
            filtered.append(doc)

    print(f"[RBAC] Docs after filter: {len(filtered)}")

    return filtered