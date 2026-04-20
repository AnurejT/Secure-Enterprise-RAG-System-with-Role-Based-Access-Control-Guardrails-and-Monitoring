def rbac_filter(documents, user_role):
    user_role = user_role.lower()

    print(f"\n[RBAC] Filtering for role: {user_role}")

    if user_role == "admin":
        return documents

    filtered_docs = []

    for doc in documents:
        roles = [r.lower() for r in doc.metadata.get("role_allowed", [])]

        print("DOC ROLES:", roles)

        if "all" in roles:
            filtered_docs.append(doc)
            continue

        if user_role in roles:
            filtered_docs.append(doc)

    print("FINAL DOC COUNT:", len(filtered_docs))

    return filtered_docs


filter_docs_by_role = rbac_filter