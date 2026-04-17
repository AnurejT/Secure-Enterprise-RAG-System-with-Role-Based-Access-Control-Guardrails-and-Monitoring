def rbac_filter(documents, user_role):
    """
    Filters documents based on user role.
    If no role_allowed metadata is set, the doc is accessible to all.
    """
    filtered_docs = []

    for doc in documents:
        allowed_roles = doc.metadata.get("role_allowed", [])

        # If no restriction set, allow all
        if not allowed_roles:
            filtered_docs.append(doc)
            continue

        # Normalize
        allowed_roles = [r.lower() for r in allowed_roles]

        if user_role.lower() in allowed_roles or "all" in allowed_roles:
            filtered_docs.append(doc)

    return filtered_docs


# Alias used by rag_service.py
filter_docs_by_role = rbac_filter