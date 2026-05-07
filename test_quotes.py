import requests
import jwt
import datetime

payload = {
    'email': 'admin@company.com',
    'role': 'admin',
    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2),
}
token = jwt.encode(payload, 'enterprise-rag-secret-key-2026', algorithm='HS256')

query = "'How did brand awareness growth (15%) compare to customer engagement growth (5%) in 2024?'"
res2 = requests.post('http://localhost:5000/api/query_stream', 
                    json={'query': query, 'role': 'admin'}, 
                    headers={'Authorization': f'Bearer {token}'},
                    stream=True)
print(res2.status_code)
print(res2.text)
