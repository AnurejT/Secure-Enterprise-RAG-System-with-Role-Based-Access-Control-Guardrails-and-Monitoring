import requests
import json

# create a dummy user and get a token by directly querying the DB, or just query without token if not required?
# We have a token from the previous script run because I can just import it.
import sys
sys.path.append(".")
from backend.core.security import generate_token

token = generate_token("admin@test.com", "admin")

query = "How did brand awareness growth (15%) compare to customer engagement growth (5%) in 2024?"
res = requests.post("http://localhost:5000/api/query_stream", 
                    json={"query": query, "role": "admin"}, 
                    headers={"Authorization": f"Bearer {token}"})
print(res.status_code)
print(res.text)
