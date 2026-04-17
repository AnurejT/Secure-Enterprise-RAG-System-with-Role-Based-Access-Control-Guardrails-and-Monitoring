from langchain_chroma import Chroma


def create_vector_store(docs, embeddings):

    db = Chroma.from_documents(
        docs,
        embedding=embeddings,
        persist_directory="vector_db"
    )

    print("[DB] Data stored in vector_db/")

    return db


def load_vector_store(embeddings):
    return Chroma(
        persist_directory="vector_db",
        embedding_function=embeddings
    )