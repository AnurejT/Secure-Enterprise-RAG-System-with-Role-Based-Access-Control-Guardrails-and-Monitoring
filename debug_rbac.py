import warnings
warnings.filterwarnings("ignore")

from rag.vector_store import load_vector_store
from rag.embeddings import get_embeddings
from rbac.access_control import rbac_filter

embeddings = get_embeddings()
db = load_vector_store(embeddings)

query = "What are the requirements for an expense above $5,000, and when is salary processed?"
docs = db.similarity_search(query, k=10)

print("=== ALL RETRIEVED DOCS ===")
for i, d in enumerate(docs):
    roles = d.metadata.get("role_allowed")
    text = d.page_content[:200].replace("\n", " ")
    print(f"\nChunk {i+1}: roles={roles}")
    print(f"  TEXT: {text}")

print("\n\n=== AFTER RBAC (finance) ===")
fdocs = rbac_filter(docs, "finance")
for i, d in enumerate(fdocs):
    print(f"\nChunk {i+1}: {d.page_content[:200].replace(chr(10),' ')}")

print(f"\nFinance sees: {len(fdocs)} docs")

print("\n\n=== AFTER RBAC (admin) ===")
adocs = rbac_filter(docs, "admin")
print(f"Admin sees: {len(adocs)} docs")
