from backend.app import create_app
from backend.services.rag_pipeline import process_query

app = create_app()
with app.app_context():
    try:
        res = process_query("How did brand awareness growth (15%) compare to customer engagement growth (5%) in 2024?", role="admin")
        print("Success:", res)
    except Exception as e:
        print("Error:", repr(e))
