import os
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    CSVLoader,
    UnstructuredExcelLoader,
    TextLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rag.vector_store import get_vector_store
from rag.embeddings import get_embeddings

def ingest_document(file_path, role):
    """
    Generic ingestion function supporting PDF, DOCX, CSV, XLSX, and MD.
    Extracted from file extension.
    """
    print("\n================ INGESTION START ================")
    print("[FILE]:", file_path)
    print("[ROLE]:", role)

    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        # =========================
        # LOAD DOCUMENT
        # =========================
        if ext == ".pdf":
            loader = PyPDFLoader(file_path)
        elif ext == ".docx":
            loader = Docx2txtLoader(file_path)
        elif ext == ".csv":
            loader = CSVLoader(file_path)
        elif ext == ".xlsx" or ext == ".xls":
            loader = UnstructuredExcelLoader(file_path, mode="elements")
        elif ext == ".md":
            loader = TextLoader(file_path, encoding="utf-8")
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        documents = loader.load()
        print(f"[LOADED DOCS]: {len(documents)}")

        # =========================
        # SPLIT INTO CHUNKS
        # =========================
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
        chunks = splitter.split_documents(documents)
        print(f"[CHUNKS CREATED]: {len(chunks)}")

        # =========================
        # ADD METADATA
        # =========================
        for i, chunk in enumerate(chunks):
            chunk.metadata["role_allowed"] = [role.lower()]
            chunk.metadata["source"] = file_path
            if "page" not in chunk.metadata:
                chunk.metadata["page"] = i // 2 

        # =========================
        # STORE IN VECTOR DB
        # =========================
        embeddings = get_embeddings()
        vector_db = get_vector_store(embeddings)
        vector_db.add_documents(chunks)

        print(f"\n[INGEST COMPLETE] Stored {len(chunks)} chunks")
        print("================================================\n")
        return True

    except Exception as e:
        print(f"\n[INGEST ERROR] {str(e)}")
        raise e

def ingest_pdf(file_path, role):
    return ingest_document(file_path, role)