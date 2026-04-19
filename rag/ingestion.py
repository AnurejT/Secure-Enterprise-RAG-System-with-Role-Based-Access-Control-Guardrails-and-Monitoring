# rag/ingestion.py

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.embeddings import get_embeddings
from rag.vector_store import create_vector_store


# ─── Role detection ─────────────────────────────────────────────────────────
# Keyword sets per role — ordered from most-specific to least-specific
ROLE_KEYWORDS = {
    "finance":     ["finance", "budget", "expense", "revenue", "cost", "profit",
                   "invoice", "payroll", "audit", "fiscal", "accounting", "cash flow"],
    "hr":          ["human resources", "recruitment", "onboarding", "performance review",
                   "leave policy", "termination", "hr department", "employee handbook"],
    "marketing":   ["marketing", "campaign", "branding", "promotion", "advertising",
                   "social media post", "seo", "lead generation", "email marketing"],
    "engineering": ["engineering", "software development", "architecture", "api",
                   "deployment", "codebase", "microservice", "ci/cd"],
}

# Filename → role mapping (highest priority — most reliable signal)
FILENAME_ROLE_MAP = {
    "finance":     "finance",
    "budget":      "finance",
    "expense":     "finance",
    "payroll":     "finance",
    "hr":          "hr",
    "human_resource": "hr",
    "recruitment": "hr",
    "marketing":   "marketing",
    "campaign":    "marketing",
    "branding":    "marketing",
    "engineering": "engineering",
    "technical":   "engineering",
    "software":    "engineering",
}


def detect_roles_from_filename(file_path):
    """Return a single role if the filename clearly indicates a department."""
    if not file_path:
        return None
    name = file_path.replace("\\", "/").split("/")[-1].lower()
    for keyword, role in FILENAME_ROLE_MAP.items():
        if keyword in name:
            return role
    return None


def detect_roles(text, file_path=None):
    """Strict role detection — filename takes priority, then keyword counts."""

    # ── 1. Filename is the strongest signal ──────────────────────────────────
    filename_role = detect_roles_from_filename(file_path)
    if filename_role:
        return [filename_role, "admin"]

    # ── 2. Keyword count per role ────────────────────────────────────────────
    text_lower = text.lower()
    scores = {}
    for role, keywords in ROLE_KEYWORDS.items():
        # Use multi-word phrases as exact substring matches (more precise)
        scores[role] = sum(1 for kw in keywords if kw in text_lower)

    max_score = max(scores.values(), default=0)

    # ── 3. Require a clear winner — must have ≥2 hits AND beat runner-up ────
    MINIMUM_HITS = 2
    if max_score < MINIMUM_HITS:
        return ["admin"]  # Too ambiguous → restrict to admin only

    winning_roles = [
        role for role, score in scores.items()
        if score == max_score
    ]

    # If there's a tie between roles (e.g. 3 finance hits, 3 marketing hits),
    # restrict to admin because we cannot safely determine ownership.
    if len(winning_roles) > 1:
        return ["admin"]

    detected_roles = set(winning_roles)
    detected_roles.add("admin")
    return list(detected_roles)



def detect_department(roles):
    # Just pick first non-admin role as department
    for role in roles:
        if role != "admin":
            return role
    return "general"




def ingest_pdf(file_path):
    """
    Ingest a PDF file into the vector database with RBAC metadata
    """

    # 1. Load PDF
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    print(f"[INFO] Loaded {len(documents)} pages from {file_path}")

    # 2. Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = splitter.split_documents(documents)

    print(f"[INFO] Created {len(chunks)} chunks")

    # 3. 🔐 Attach RBAC metadata (FIXED)
    for chunk in chunks:
        content = chunk.page_content

        roles = detect_roles(content, file_path=file_path)
        department = detect_department(roles)

        chunk.metadata["role_allowed"] = roles
        chunk.metadata["department"] = department
        chunk.metadata["source"] = file_path

    print(f"[INFO] RBAC metadata assigned to all chunks")

    # 🔍 DEBUG (VERY IMPORTANT)
    print("\n[DEBUG] Sample metadata:")
    for i in range(min(3, len(chunks))):
        print(chunks[i].metadata)

    # 4. Create embeddings
    embeddings = get_embeddings()

    # 5. Store in Vector DB
    vector_db = create_vector_store(chunks, embeddings)

    print(f"[INFO] Stored in vector database successfully")

    return vector_db