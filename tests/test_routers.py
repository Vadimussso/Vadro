from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


def test_read_ads():
    response = client.get("/ads")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def read_ad():
    response = client.get("/ads/1")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_registration(user_data):
    response = client.post(
        "/users/registration",
        json=user_data
    )
    assert response.status_code == 200
    assert response.json() == {"message": "User registered successfully"}


def test_login():
    response = client.post()