import psycopg2
import pytest

from fastapi.testclient import TestClient
from main import app
from config import settings
from psycopg2.extras import RealDictCursor
from main import make_user, login, UserCreate, LogIn
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


@pytest.fixture(scope='function')
def get_test_db_connection():
    conn = psycopg2.connect(settings.database_url, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture(scope='function')
def make_user_token(user_data, get_test_db_connection):
    con = get_test_db_connection
    make_user(UserCreate(**user_data), con)
    response = login(LogIn(email=user_data["email"], password=user_data["password"]), con)
    token = response["token"]

    return token


@pytest.fixture(scope='function')
def make_admin_token(admin_user_data, get_test_db_connection):
    con = get_test_db_connection
    make_user(UserCreate(**admin_user_data), con)
    response = login(LogIn(email=admin_user_data["email"], password=admin_user_data["password"]), con)
    token = response["token"]

    return token





