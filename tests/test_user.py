import pytest


def test_registration(client, user_data):
    response = client.post(
        "/users/registration",
        json=user_data
    )
    assert response.status_code == 200


@pytest.mark.parametrize("wrong_email, wrong_password, status",
                         [(True, False, 400),
                          (False, True, 400),
                          (False, False, 200)
                          ])
def test_login(client, wrong_email, wrong_password, status, user_data):
    response_registration = client.post(
        "/users/registration",
        json=user_data
    )

    assert response_registration.status_code == 200

    email = user_data["email"]
    password = user_data["password"]

    if wrong_email:
        email = "dummy_email@example.com"

    if wrong_password:
        password = "dummy_password"

    response = client.post(
        "/users/login",
        json={'email': email, 'password': password})

    assert response.status_code == status
