from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.embeddings import get_embeddings
from rag.vector_store import create_vector_store


# 🔥 Detect role from content
def detect_role(text):
    text = text.lower()

    if "hr department" in text:
        return ["hr", "admin"]
    elif "finance department" in text:
        return ["finance", "admin"]
    elif "engineering department" in text:
        return ["engineering", "admin"]
    elif "marketing department" in text:
        return ["marketing", "admin"]
    else:
        return ["admin"]


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

    # 3. 🔐 Attach RBAC metadata dynamically
    for chunk in chunks:
        content = chunk.page_content

        roles = detect_role(content)

        chunk.metadata["role_allowed"] = roles
        chunk.metadata["source"] = file_path

    print(f"[INFO] RBAC metadata assigned to all chunks")

    # 4. Create embeddings
    embeddings = get_embeddings()

    # 5. Store in Vector DB
    vector_db = create_vector_store(chunks, embeddings)

    print(f"[INFO] Stored in vector database successfully")

    return vector_db