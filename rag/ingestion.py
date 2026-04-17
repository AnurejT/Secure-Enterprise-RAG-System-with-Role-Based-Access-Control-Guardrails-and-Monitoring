from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.embeddings import get_embeddings
from rag.vector_store import create_vector_store


def ingest_pdf(file_path):

    # 1. Load PDF
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    print(f"Loaded {len(documents)} pages")

    # 2. Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = splitter.split_documents(documents)

    print(f"Created {len(chunks)} chunks")

    # 3. Add Metadata (RBAC Ready 🔐)
    for chunk in chunks:
        chunk.metadata["role_allowed"] = ["finance"]   # change later dynamically
        chunk.metadata["department"] = "finance"
        chunk.metadata["source"] = file_path

    # 4. Create embeddings
    embeddings = get_embeddings()

    # 5. Store in Vector DB
    vector_db = create_vector_store(chunks, embeddings)

    return vector_db