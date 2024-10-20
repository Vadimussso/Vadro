from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from pydantic import BaseModel, EmailStr
from config import settings

app = FastAPI()

auth_scheme = HTTPBearer()


class UserBase(BaseModel):
    email: EmailStr
    name: str
    surname: str


class UserCreate(UserBase):
    password: str
    is_admin: bool


class User(UserBase):
    id: int
    is_admin: bool


class LogIn(BaseModel):
    email: str
    password: str


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


def get_db():
    conn = psycopg2.connect(settings.database_url, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()


def make_user(user: UserCreate, db):
    with db.cursor() as cursor:
        cursor.execute(
            """INSERT INTO users (email, name, surname, password, is_admin, created_at) 
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id, email, name, surname, is_admin""",
            (user.email, user.name, user.surname, user.password, user.is_admin, datetime.now())
        )
        db.commit()

        created_user = cursor.fetchone()
    return User(**created_user)


@app.post("/users/registration")
def registration(user: UserCreate, db=Depends(get_db)):
    new_user = make_user(user, db)
    return {"user_id": new_user.id, "message": "User registered successfully"}


def get_current_user(credentials: HTTPAuthorizationCredentials):

    token = credentials.credentials

    conn = psycopg2.connect(settings.database_url, cursor_factory=RealDictCursor)

    try:
        with conn.cursor() as cursor:
            # check whether the user is registered
            cursor.execute(
                """
                SELECT id, email, name, surname, is_admin FROM users 
                WHERE token = %s
                """,
                (token,)
            )
            user_data = cursor.fetchone()
    finally:
        conn.close()

    if user_data is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    return User(**user_data)


@app.middleware("http")
async def add_user(request: Request, call_next):

    # Initialize the user in the request state
    request.state.user = None

    if "Authorization" in request.headers:
        credentials: HTTPAuthorizationCredentials = await auth_scheme(request)
        try:
            user = get_current_user(credentials)
            request.state.user = user
        except HTTPException:
            pass

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
            ) RETURNING id
            """,
            (
                datetime.now(), ad.vin, ad.vrc, ad.license_plate, ad.brand,
                ad.model, ad.mileage, ad.engine_capacity, ad.price,
                ad.description, ad.city, ad.phone, datetime.now(), request.state.user.id
            )
        )
        db.commit()

        add_id = cursor.fetchone()['id']

    return {"message": "Ad applied successfully", "id": add_id}


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
    if request.state.user is None or not request.state.user.is_admin:
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



