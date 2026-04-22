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


def delete_doc_from_db(file_path, embeddings):
    """Purges all chunks associated with a specific file path from the vector store."""
    from langchain_chroma import Chroma
    db = Chroma(
        persist_directory="vector_db",
        embedding_function=embeddings
    )
    # In LangChain's Chroma wrapper, we can delete by metadata filter
    # Note: version dependent, but usually 'filter' or 'where'
    db.delete(where={"source": file_path})
    print(f"[DB] Purged all chunks for: {file_path}")