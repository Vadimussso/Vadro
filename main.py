from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from pydantic import BaseModel, EmailStr
from config import settings

app = FastAPI()


class User(BaseModel):
    email: EmailStr
    name: str
    surname: str
    password: str


auth_scheme = HTTPBearer()


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
    conn = psycopg2.connect(settings.database_url, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()


@app.middleware("http")
async def add_user(request: Request, call_next):

    # Initialize the user in the request state
    request.state.user = None

    try:
        # Try to retrieve credentials using the auth scheme
        security: HTTPAuthorizationCredentials = await auth_scheme(request)
        if not security.credentials:
            # if there is no token, or it is empty, pass the request further
            return await call_next(request)
    except HTTPException:
        # If the Authorization header is missing or invalid, continue without raising an error
        return await call_next(request)

    # If there is token, connect to db
    conn = psycopg2.connect(settings.database_url, cursor_factory=RealDictCursor)
    try:
        user = fetch_user(conn, security.credentials)
    finally:
        conn.close()

    request.state.user = user

    response = await call_next(request)
    return response


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


@app.post("/ads")
def add_ad(ad: Ad, request: Request, db=Depends(get_db)):

    # if no id and person is not registered return Error
    if request.state.user is None:
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
                ad.description, ad.city, ad.phone, datetime.now(), request.state.user.id
            )
        )
        db.commit()

    return {"message": "Ad applied successfully"}


@app.post("/ads/{item_id}/moderate")
def moderate(item_id: int, request: Request, db=Depends(get_db)):

    # Check id the ad exists
    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT id FROM ads WHERE id = %s
            """,
            [item_id]
        )
        ad = cursor.fetchone()

    if ad is None:
        raise HTTPException(status_code=404, detail="Item not found")

    # if nothing is returned, an error is returned.
    if request.state.user is None or request.state.user.is_admin is False:
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



