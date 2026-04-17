# rag/ingestion.py

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.embeddings import get_embeddings
from rag.vector_store import create_vector_store


# 🔥 Strong keyword-based role detection
ROLE_KEYWORDS = {
    "hr": ["hr", "human resources", "employee", "recruitment", "salary", "leave"],
    "finance": ["finance", "budget", "expense", "revenue", "cost", "profit"],
    "engineering": ["engineering", "development", "software", "system", "architecture"],
    "marketing": ["marketing", "campaign", "branding", "promotion", "sales"],
}


def detect_roles(text):
    text = text.lower()
    detected_roles = set()

    for role, keywords in ROLE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                detected_roles.add(role)

    # ✅ If nothing detected → restrict access (SAFE DEFAULT)
    if not detected_roles:
        return ["admin"]   # Only admin can access unknown content

    # ✅ Always allow admin access
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

        roles = detect_roles(content)
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