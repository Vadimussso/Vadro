import psycopg2
from config import settings
from psycopg2.extras import RealDictCursor


def get_db():
    conn = psycopg2.connect(settings.database_url, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()