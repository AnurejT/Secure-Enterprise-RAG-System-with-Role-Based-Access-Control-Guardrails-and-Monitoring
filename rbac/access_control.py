def rbac_filter(documents, user_role):
    """
    Filters documents based on user role
    """

    filtered_docs = []

    for doc in documents:
        allowed_roles = doc.metadata.get("role_allowed", [])

        # Normalize (important)
        allowed_roles = [r.lower() for r in allowed_roles]

        if user_role.lower() in allowed_roles or "all" in allowed_roles:
            filtered_docs.append(doc)

    return filtered_docs