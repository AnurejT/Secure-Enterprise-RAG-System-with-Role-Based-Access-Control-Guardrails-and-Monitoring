import warnings
warnings.filterwarnings("ignore")

from rag.vector_store import load_vector_store
from rag.embeddings import get_embeddings
from rbac.access_control import rbac_filter

db = load_vector_store(get_embeddings())
results = db.similarity_search("5,000", k=20)

for i, d in enumerate(results):
    if "5,000" in d.page_content or "5000" in d.page_content:
        print(f"MATCH: roles={d.metadata.get('role_allowed')}")
        print(d.page_content.strip())
        print("-" * 50)
