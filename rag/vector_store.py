def create_vector_store(docs, embeddings):
    from langchain_chroma import Chroma

    db = Chroma(
        persist_directory="vector_db",
        embedding_function=embeddings
    )

    db.add_documents(docs)  # ✅ Append instead of overwrite
    print("[DB] Data added to vector_db/")

    return db


def load_vector_store(embeddings):
    from langchain_chroma import Chroma
    return Chroma(
        persist_directory="vector_db",
        embedding_function=embeddings
    )


def get_vector_store(embeddings):
    """Convenience alias for load_vector_store used in ingestion.py"""
    return load_vector_store(embeddings)