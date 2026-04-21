# rag/ingestion.py

import os
import shutil
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.embeddings import get_embeddings
from rag.vector_store import create_vector_store


# ─── RESET VECTOR DB ─────────────────────────
def reset_vector_db():
    if os.path.exists("vector_db"):
        shutil.rmtree("vector_db")
        print("[RESET] Old vector DB deleted")


# ─── RULE-BASED ROLE DETECTION (VERY IMPORTANT) ─────────────
def detect_role(text):
    t = text.lower()

    if any(w in t for w in ["$", "budget", "expense", "payment", "approval", "cost"]):
        return "finance"

    if any(w in t for w in ["salary", "employee", "leave", "recruitment", "hr"]):
        return "hr"

    if any(w in t for w in ["ads", "campaign", "marketing", "promotion"]):
        return "marketing"

    if any(w in t for w in ["system", "software", "server", "engineering"]):
        return "engineering"

    return "general"


# ─── MAIN INGEST ─────────────────────────────
def ingest_pdf(file_path):
    print(f"\n[INGEST] File: {file_path}")

    reset_vector_db()

    loader = PyPDFLoader(file_path)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=80
    )

    chunks = splitter.split_documents(documents)

    print(f"[INFO] Total chunks: {len(chunks)}")

    for i, chunk in enumerate(chunks):
        role = detect_role(chunk.page_content)

        chunk.metadata["role_allowed"] = [role, "admin"]
        chunk.metadata["department"] = role
        chunk.metadata["source"] = file_path

        # DEBUG
        if i < 5:
            print("\n[CHUNK]")
            print(chunk.page_content[:120])
            print("DEPT:", role)

    embeddings = get_embeddings()
    vector_db = create_vector_store(chunks, embeddings)

    print("[INFO] Stored in vector DB")

    return vector_db