# rag/ingestion.py

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.embeddings import get_embeddings
from rag.vector_store import create_vector_store


# ─── ROLE KEYWORDS ─────────────────────────────────────────────
ROLE_KEYWORDS = {
    "finance": [
        "finance", "budget", "expense", "revenue", "cost",
        "profit", "invoice", "payroll", "audit", "accounting",
        "reimbursement", "deduction", "tax", "salary"
    ],
    "hr": [
        "human resources", "recruitment", "onboarding",
        "leave policy", "employee conduct", "code of conduct",
        "workplace", "disciplinary", "hr head", "probation"
    ],
    "marketing": [
        "marketing", "campaign", "branding", "seo",
        "advertising", "social media", "customer acquisition",
        "conversion rate", "roas", "cac", "ad spend",
        "digital campaign", "performance metrics"
    ],
    "engineering": [
        "engineering", "software", "api",
        "deployment", "code review", "system architecture"
    ],
}


# ─── FILENAME-BASED ROLE DETECTION ─────────────────────────────
FILENAME_ROLE_MAP = {
    "finance": "finance",
    "budget": "finance",
    "expense": "finance",
    "payroll": "finance",
    "hr": "hr",
    "recruitment": "hr",
    "marketing": "marketing",
    "campaign": "marketing",
    "engineering": "engineering",
}


def detect_roles_from_filename(file_path):
    if not file_path:
        return None

    filename = file_path.lower()

    for keyword, role in FILENAME_ROLE_MAP.items():
        if keyword in filename:
            return role

    return None


# ─── ROLE DETECTION FROM TEXT ──────────────────────────────────
def detect_roles(text, file_path=None):

    # 1. Filename has highest priority — trust it completely
    filename_role = detect_roles_from_filename(file_path)
    if filename_role:
        return [filename_role, "admin"]

    text_lower = text.lower()
    scores = {}

    # 2. Keyword scoring
    for role, keywords in ROLE_KEYWORDS.items():
        scores[role] = sum(1 for kw in keywords if kw in text_lower)

    max_score = max(scores.values(), default=0)

    # 3. Require a meaningful score (≥2 keyword hits) to assign a role
    #    Prevents a single stray keyword from mis-tagging a chunk
    MIN_SCORE = 2
    if max_score < MIN_SCORE:
        return ["all"]

    # 4. STRICT: only include roles that hit the maximum score
    winning_roles = [role for role, score in scores.items() if score == max_score]

    # 5. Tie-breaking: if multiple roles share the top score,
    #    check if one is clearly dominant (beats all others by ≥ 2)
    if len(winning_roles) > 1:
        true_winner = None
        for role in winning_roles:
            role_score = scores[role]
            others = [scores[r] for r in scores if r != role]
            if all(role_score - s >= 2 for s in others):
                true_winner = role
                break

        if true_winner:
            # Clear winner — assign only that role
            winning_roles = [true_winner]
        else:
            # Genuine tie — the chunk spans multiple departments, so allow all tied roles
            pass

    detected_roles = set(winning_roles)
    detected_roles.add("admin")

    return list(detected_roles)


# ─── DEPARTMENT DETECTION ──────────────────────────────────────
def detect_department(roles):
    for role in roles:
        if role not in ["admin", "all"]:
            return role
    return "general"


# ─── MAIN INGEST FUNCTION ──────────────────────────────────────
def ingest_pdf(file_path):
    print(f"\n[INGEST] Ingesting file: {file_path}")

    # 1. Load PDF
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    print(f"[INFO] Loaded {len(documents)} pages")

    # 🔥 2. Improved chunking (VERY IMPORTANT)
    # Reduced chunk size prevents cross-department leakage
    # (e.g. merging HR and Finance paragraphs into a single chunk)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=50
    )

    chunks = splitter.split_documents(documents)

    print(f"[INFO] Created {len(chunks)} chunks")

    # 3. Attach metadata
    for i, chunk in enumerate(chunks):
        content = chunk.page_content

        roles = detect_roles(content, file_path)
        department = detect_department(roles)

        chunk.metadata["role_allowed"] = [r.lower() for r in roles]
        chunk.metadata["department"] = department
        chunk.metadata["source"] = file_path

        # [DEBUG] Debug sample
        if i < 5:
            print("[DEBUG] SAMPLE CHUNK METADATA:")
            print(chunk.metadata)

    print(f"\n[INFO] Metadata assigned to all chunks")

    # 4. Create embeddings
    embeddings = get_embeddings()

    # 5. Store in vector DB
    vector_db = create_vector_store(chunks, embeddings)

    print(f"[INFO] Stored in vector database successfully")

    return vector_db