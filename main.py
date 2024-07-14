from fastapi import FastAPI, Depends
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://app:app@localhost:5432/app"

def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()


app = FastAPI()


@app.get("/ads")
def read_ads(db=Depends(get_db)):
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM ads")
        items = cursor.fetchall()
        return items

