import pytest

from fastapi.testclient import TestClient
from main import app
from main import UserCreate, UserCredentials
from .fabrics import ad_fabric, user_fabric


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture
def ad_data():
    return ad_fabric()


@pytest.fixture(scope='function')
def user_data():
    return user_fabric(is_admin=False)


@pytest.fixture(scope='function')
def admin_user_data():
    return user_fabric(is_admin=True)


# @pytest.fixture(scope='function')
# def get_test_db_connection():
#     conn = psycopg2.connect(settings.database_url, cursor_factory=RealDictCursor)
#     try:
#         yield conn
#     finally:
#         conn.close()


# @pytest.fixture(scope='function')
# def make_user_token(user_data, get_test_db_connection):
#     con = get_test_db_connection
#     registration(UserCreate(**user_data), con)
#     response = login(UserCredentials(email=user_data["email"], password=user_data["password"]), con)
#     token = response["token"]
#
#     return token

@pytest.fixture(scope='function')
def make_user_token(client, user_data):
    # registration
    client.post("/users/registration", json=user_data)

    # getting a token

    user_credentials = {
        "email": user_data["email"],
        "password": user_data["password"]
    }

    response_login = client.post("/users/login", json=user_credentials)
    token = response_login.json()["token"]

    return token


@pytest.fixture(scope='function')
def make_admin_token(client, admin_user_data):

    # registration
    client.post("/users/registration", json=admin_user_data)

    # getting a token
    user_credentials = {
        "email": admin_user_data["email"],
        "password": admin_user_data["password"]
    }

    response_login = client.post("/users/login", json=user_credentials)

    token = response_login.json()["token"]

    return token
