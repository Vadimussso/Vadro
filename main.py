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


class Car(BaseModel):
    vin: str
    vrc: str
    license_plate: str
    brand: str
    model: str
    mileage: int
    engine_capacity: int
    price: int
    description: str
    city: str
    phone: str
    posted_at: str


class CurrentUser(BaseModel):
    id: int
    email: str
    name: str
    surname: str
    is_admin: bool


def fetch_user(db, token: str) -> None | CurrentUser:
    with db.cursor() as cursor:
        # check whether the user is registered and is_admin
        cursor.execute(
            """
            SELECT id, email, name, surname, is_admin FROM users 
            WHERE token = %s
            """,
            (token,)
        )
        user = cursor.fetchone()

    if user is None:
        return
    return CurrentUser(**user)


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
        cursor.execute(
            """SELECT vin, vrc, license_plate, brand, model, mileage, engine_capacity, price, description, city, phone, posted_at
            FROM ads
            WHERE is_moderated = true
            """)
        items = cursor.fetchall()
        return items


@app.get("/ads/{item_id}")
def read_ad(item_id, db=Depends(get_db)):
    with db.cursor() as cursor:
        cursor.execute(
            """SELECT vin, vrc, license_plate, brand, model, mileage, engine_capacity, price, description, city, phone, posted_at
             FROM ads 
             WHERE id = %s AND is_moderated = true
             """, [item_id])
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
        # pull token from the database using login and password
        cursor.execute(
            "SELECT token FROM users WHERE email = %s AND password = %s",
            (login.email, login.password)
        )
        res = cursor.fetchone()

    # if nothing is returned then we return an error
    if res is None:
        raise HTTPException(status_code=400, detail="Wrong email or password")
    # otherwise we return the token
    return res


class Ad(BaseModel):
    vin: str
    vrc: str
    license_plate: str
    brand: str
    model: str
    mileage: int
    engine_capacity: int
    price: int
    description: str
    city: str
    phone: str


class Token(BaseModel):
    token: str


@app.post("/ads")
def add_ad(ad: Ad, token: Token, db=Depends(get_db)):

    user = fetch_user(db, token.token)

    # if no id and person is not registered return Error
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # if id exist, ad applying is carry on
    with db.cursor() as cursor:
        # attempt to apply the ad:
        cursor.execute(
            """
            INSERT INTO ads (
                created_at, vin, vrc, license_plate, brand, model, mileage, 
                engine_capacity, price, description, city, phone, posted_at, author_id
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """,
            (
                datetime.now(), ad.vin, ad.vrc, ad.license_plate, ad.brand,
                ad.model, ad.mileage, ad.engine_capacity, ad.price,
                ad.description, ad.city, ad.phone, datetime.now(), user.id
            )
        )
        db.commit()

    return {"message": "Ad applied successfully"}


@app.post("/ads/{item_id}/moderate")
def moderate(item_id, token: Token, db=Depends(get_db)):

    user = fetch_user(db, token.token)

    # if nothing is returned, an error is returned.
    if user is None or user.is_admin is False:
        raise HTTPException(status_code=403, detail="Forbidden")

    # if id exists, moderation is allowed
    with db.cursor() as cursor:
        cursor.execute(
            """
            UPDATE ads SET is_moderated = true
            WHERE id = %s
            """,
            [item_id]
        )

        db.commit()

    return {"message": "moderation_completed"}



