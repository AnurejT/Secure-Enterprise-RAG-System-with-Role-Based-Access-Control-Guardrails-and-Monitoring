"""
Re-ingest all PDFs from the data/ folder into vector_db/.
Run this after adding new documents or changing role detection logic.

Usage:
    python ingest.py
"""

import os
from rag.ingestion import ingest_pdf

DATA_DIR = "data"

if __name__ == "__main__":
    pdf_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".pdf")]

    if not pdf_files:
        print("[ERROR] No PDF files found in data/ folder.")
    else:
        for pdf in pdf_files:
            path = os.path.join(DATA_DIR, pdf)
            print(f"\n[INGEST] Processing: {path}")
            ingest_pdf(path)
            print(f"[INGEST] Done: {pdf}")

    print("\n[INGEST] All documents ingested into vector_db/")
