from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_read_ads():
    response = client.get("/ads")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_registration():
    response = client.post(
        "/users/registration",
        json={
            "email": "test@example.com",
            "name": "Test",
            "surname": "User",
            "password": "securepassword"
        }
    )
    assert response.status_code == 200
    assert response.json() == {"message": "User registered successfully"}