import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from backend.rag.ingestion.document_ingestor import ingest_document
from backend.repositories.vector_repo import delete_by_source
from backend.rag.embeddings.encoder import get_embeddings

csv_path = os.path.abspath(r"storage\documents\raw\hr_data.csv")
role = "hr"

if not os.path.exists(csv_path):
    print(f"Error: {csv_path} not found.")
else:
    print(f"Cleaning up vector store for: {csv_path}")
    delete_by_source(csv_path, get_embeddings())
    
    print(f"Re-ingesting: {csv_path}")
    ingest_document(csv_path, role)
    print("Re-ingestion complete.")
