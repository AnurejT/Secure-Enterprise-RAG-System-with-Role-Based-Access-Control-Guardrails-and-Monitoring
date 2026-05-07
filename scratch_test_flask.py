from backend.app import create_app
from backend.core.extensions import db
from backend.models.user import User

app = create_app()

with app.app_context():
    # create a dummy user
    u = User.query.filter_by(email="admin@test.com").first()
    if not u:
        u = User()
        u.name = "admin test"
        u.email = "admin@test.com"
        u.password_hash = "dummy"
        u.role = "admin"
        db.session.add(u)
        db.session.commit()
    
    from backend.core.security import generate_token
    token = generate_token("admin@test.com", "admin")

    client = app.test_client()
    query = ".s"
    
    response = client.post("/api/query_stream", 
                           json={"query": query, "role": "admin"},
                           headers={"Authorization": f"Bearer {token}"})
    
    print("Status code:", response.status_code)
    try:
        print("Response text:", response.get_data(as_text=True))
    except Exception as e:
        print("Error getting data:", repr(e))
