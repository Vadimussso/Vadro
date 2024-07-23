from fastapi import FastAPI, Depends, HTTPException
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from pydantic import BaseModel, EmailStr


class User(BaseModel):
    email: EmailStr
    name: str
    surname: str
    password: str


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


@app.get("/ads/{item_id}")
def read_ad(item_id, db=Depends(get_db)):
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM ads WHERE id = %s", [item_id])
        item = cursor.fetchone()
        if item is None:
            raise HTTPException(status_code=404, detail="Item not found")
        return item


@app.post("/users/registration")
def registration(user: User, db=Depends(get_db)):
    with db.cursor() as cursor:
        cursor.execute(
            "INSERT INTO users (email, name, surname, password, created_at, is_admin) VALUES (%s, %s, %s, %s, %s, %s)",
            (user.email, user.name, user.surname, user.password, datetime.now(), False)
        )
        db.commit()
    return {"message": "User registered successfully"}


class LogIn(BaseModel):
    email: str
    password: str


@app.post("/users/login")
def login(login: LogIn, db=Depends(get_db)):
    with db.cursor() as cursor:
        # вытащить из базы token по логину и поролю
        cursor.execute(
            "SELECT token FROM users WHERE email = %s AND password = %s",
            (login.email, login.password)
        )
        res = cursor.fetchone()
    # если ничего не вернулось то возвращаем ошибку

    if res is None:
        raise HTTPException(status_code=400, detail="Wrong email or password")
    # иначе возвращаем токен
    return res

