def test_register_and_login(client):
    resp = client.post("/api/auth/register", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "StrongPass123",
        "confirm_password": "StrongPass123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data

    resp2 = client.post("/api/auth/login", json={"email": "test@example.com", "password": "StrongPass123"})
    assert resp2.status_code == 200
    assert "access_token" in resp2.json()


def test_register_password_mismatch(client):
    resp = client.post("/api/auth/register", json={
        "name": "Test User",
        "email": "mismatch@example.com",
        "password": "StrongPass123",
        "confirm_password": "Different123",
    })
    assert resp.status_code == 400
