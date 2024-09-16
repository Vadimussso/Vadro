# import pytest
# import psycopg2
# from psycopg2.extras import RealDictCursor
# from config import settings
# from fastapi.testclient import TestClient
# from main import app, get_db
#
#
# @pytest.fixture(scope="session")
# def db_connection():
#     conn = psycopg2.connect(settings.database_url, cursor_factory=RealDictCursor)
#     try:
#         yield conn
#     finally:
#         conn.close()
#
#
# @pytest.fixture
# def db_transaction(db_connection):
#     db_connection.autocommit = False
#     cursor = db_connection.cursor()
#     yield db_connection
#     db_connection.rollback()
#     cursor.close()
#
#
# @pytest.fixture
# def client(db_transaction):
#     app.dependency_overrides[get_db] = lambda: db_transaction
#     return TestClient(app)