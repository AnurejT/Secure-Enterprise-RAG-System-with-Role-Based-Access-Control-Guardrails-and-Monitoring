"""
backend/rag/ingestion/document_ingestor.py
Document parsing and chunking for all supported formats.
Moved from rag/ingestion.py; uses new repository and config paths.
"""
import os
import re

import pandas as pd
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.core.config import DOCUMENTS_DIR
from backend.rag.embeddings.encoder import get_embeddings
from backend.repositories import vector_repo

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".csv", ".xlsx", ".md"}


def _extract_employee_id(text: str) -> str | None:
    match = re.search(r"FINEMP\d+", text, re.IGNORECASE)
    return match.group(0).upper() if match else None


def ingest_document(file_path: str, role: str) -> bool:
    """
    Parse, chunk, embed, and store a document in the vector repository.
    Returns True on success, raises on failure.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}")

    role = role.lower()
    base_metadata = {
        "role_allowed": [role],
        "department":   role,
        "source":       file_path,
    }

    documents: list[Document] = []

    # ── Tabular formats (CSV / Excel) ──────────────────────────────
    if ext in (".csv", ".xlsx"):
        df = pd.read_csv(file_path) if ext == ".csv" else pd.read_excel(file_path)
        for i, row in df.iterrows():
            text = "\n".join(f"{col}: {row[col]}" for col in df.columns)
            meta = {**base_metadata, "row": int(i)}
            emp_id = _extract_employee_id(text)
            if emp_id:
                meta["employee_id"] = emp_id
            documents.append(Document(page_content=text, metadata=meta))

    # ── Markdown ───────────────────────────────────────────────────
    elif ext == ".md":
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
        for i, chunk in enumerate(splitter.split_text(content)):
            meta = {**base_metadata, "chunk_id": i}
            emp_id = _extract_employee_id(chunk)
            if emp_id:
                meta["employee_id"] = emp_id
            documents.append(Document(page_content=chunk, metadata=meta))

    # ── PDF / DOCX ─────────────────────────────────────────────────
    else:
        from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
        loader = PyPDFLoader(file_path) if ext == ".pdf" else Docx2txtLoader(file_path)
        raw_docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        for i, doc in enumerate(splitter.split_documents(raw_docs)):
            meta = {**base_metadata, "chunk_id": i}
            if "page" in doc.metadata:
                meta["page"] = doc.metadata["page"]
            emp_id = _extract_employee_id(doc.page_content)
            if emp_id:
                meta["employee_id"] = emp_id
            documents.append(Document(page_content=doc.page_content, metadata=meta))

    # ── Safety check ───────────────────────────────────────────────
    for doc in documents:
        if "role_allowed" not in doc.metadata:
            doc.metadata["role_allowed"] = [role]

    vector_repo.add_documents(documents, get_embeddings())
    print(f"[Ingestor] Stored {len(documents)} chunks for: {os.path.basename(file_path)}")
    return True
