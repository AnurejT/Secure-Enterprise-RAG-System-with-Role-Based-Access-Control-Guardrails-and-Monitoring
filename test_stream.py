import requests
import json

def test():
    # Get a token first
    res = requests.post("http://localhost:5000/api/login", json={"email": "admin@test.com", "password": "dummy"})
    if res.status_code != 200:
        print("Login failed")
        return
    token = res.json()["token"]

    query = "How did brand awareness growth (15%) compare to customer engagement growth (5%) in 2024?"
    res = requests.post("http://localhost:5000/api/query_stream", 
                        json={"query": query, "role": "admin"}, 
                        headers={"Authorization": f"Bearer {token}"},
                        stream=True)
    
    print(res.status_code)
    for chunk in res.iter_content(chunk_size=None):
        if chunk:
            print(f"CHUNK: {chunk.decode('utf-8')}")

if __name__ == "__main__":
    test()
