import warnings
warnings.filterwarnings("ignore")
from services.rag_service import process_query
from rbac.access_control import rbac_filter
from rag.retriever import get_relevant_docs

res = process_query("What are the requirements for an expense above $5,000, and when is salary processed?", "hr")
print("\n[FINAL ANSWER TO HR]:", res["answer"])

print("\n[DEBUG HR DOCS]:")
docs = get_relevant_docs("What are the requirements for an expense above $5,000, and when is salary processed?")
hr_docs = rbac_filter(docs, "hr")
for i, d in enumerate(hr_docs):
    roles = d.metadata.get("role_allowed", [])
    print(f"-- doc {i+1} -- roles: {roles} -- {str(d.page_content).strip()[:100]}...")
