from services.rag_service import process_query

def query_rag(user_query, role):
    return process_query(user_query, role)