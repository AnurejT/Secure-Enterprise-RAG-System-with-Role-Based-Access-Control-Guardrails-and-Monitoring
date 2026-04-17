from rag.vector_store import load_vector_store
from rag.embeddings import get_embeddings


def get_relevant_docs(query):

    embeddings = get_embeddings()
    vector_db = load_vector_store(embeddings)

    retriever = vector_db.as_retriever(search_kwargs={"k": 5})

    docs = retriever.invoke(query)

    return docs