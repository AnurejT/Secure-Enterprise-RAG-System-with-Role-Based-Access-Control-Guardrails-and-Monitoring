from rag.retriever import get_relevant_docs
from rbac.access_control import rbac_filter
from rag.llm import get_llm_response


def process_query(query, user_role):

    # 1. Retrieve documents
    docs = get_relevant_docs(query)

    print(f"[RAG] Retrieved {len(docs)} docs")

    # 2. Apply RBAC
    docs = rbac_filter(docs, user_role)

    print(f"[RBAC] After filter: {len(docs)} docs")

    # 3. Guard: No access
    if not docs:
        return "No information available"

    # 4. Generate response
    response = get_llm_response(query, docs)

    return response