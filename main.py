from fastapi import FastAPI
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://app:app@localhost:5432/app"

def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn


app = FastAPI()


@app.get("/ads")
def read_ads():
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM ads")
            items = cursor.fetchall()
            return items
    finally:
        conn.close()
