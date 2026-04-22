from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.vector_store import get_vector_store
from rag.embeddings import get_embeddings


def ingest_pdf(file_path, role):
    print("\n================ INGESTION START ================")
    print("[FILE]:", file_path)
    print("[ROLE]:", role)

    # =========================
    # LOAD PDF
    # =========================
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    print(f"[LOADED DOCS]: {len(documents)}")

    # =========================
    # SPLIT INTO CHUNKS
    # =========================
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = splitter.split_documents(documents)

    print(f"[CHUNKS CREATED]: {len(chunks)}")

    # =========================
    # ADD ROLE METADATA
    # =========================
    for i, chunk in enumerate(chunks):
        chunk.metadata["role_allowed"] = [role.lower()]
        chunk.metadata["source"] = file_path

        print(f"\n[CHUNK {i+1}]")
        print("Preview:", chunk.page_content[:100])
        print("Metadata:", chunk.metadata)

    # =========================
    # STORE IN VECTOR DB
    # =========================
    embeddings = get_embeddings()
    vector_db = get_vector_store(embeddings)

    vector_db.add_documents(chunks)

    print(f"\n[INGEST COMPLETE] Stored {len(chunks)} chunks")
    print("================================================\n")