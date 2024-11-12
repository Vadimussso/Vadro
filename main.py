from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from pydantic import BaseModel, EmailStr
from config import settings
from typing import Protocol

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


class UserCredentials(BaseModel):
    email: EmailStr
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


class UserRequiredError(ValueError):
    def __init__(self, message="User is required"):
        super().__init__(message)


class UserCredentialsError(ValueError):

    def __init__(self, message="Wrong credentials"):
        super().__init__(message)


class ItemRequiredError(ValueError):
    def __init__(self, message="Item is not represented"):
        super().__init__(message)


def get_db():
    conn = psycopg2.connect(settings.database_url, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()


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


class UserRepoProtocol(Protocol):

    def make_user(self, user: UserCreate) -> User:
        pass

    def login(self, credentials: UserCredentials) -> dict:
        pass


class UserRepo:

    def __init__(self, db=Depends(get_db)):
        self.db = db

    def make_user(self, user: UserCreate) -> User:
        with self.db.cursor() as cursor:
            cursor.execute(
                """INSERT INTO users (email, name, surname, password, is_admin, created_at) 
                   VALUES (%s, %s, %s, %s, %s, %s) 
                   RETURNING id, email, name, surname, is_admin
                   """,
                (user.email, user.name, user.surname, user.password, user.is_admin, datetime.now())
            )
            self.db.commit()

            created_user = cursor.fetchone()
        return User(**created_user)

    def login(self, credentials: UserCredentials) -> dict | None:
        with self.db.cursor() as cursor:
            # pull token from the database using login and password
            cursor.execute(
                "SELECT token FROM users WHERE email = %s AND password = %s",
                (credentials.email, credentials.password)
            )
            res = cursor.fetchone()
        return res


class UserServiceProtocol(Protocol):

    def make_user(self, user: UserCreate) -> User:
        pass

    def login(self, credentials: UserCredentials) -> dict | None:
        pass


class UserService:

    def __init__(self, user_repo: UserRepoProtocol = Depends(UserRepo)):
        self.user_repo = user_repo

    def make_user(self, user: UserCreate) -> User:
        return self.user_repo.make_user(user)

    def login(self, credentials: UserCredentials) -> dict:

        token = self.user_repo.login(credentials)

        if not token:
            raise UserCredentialsError()

        return token


@app.post("/users/registration")
def registration(user: UserCreate, user_service: UserServiceProtocol = Depends(UserService)) -> dict:
    new_user = user_service.make_user(user)

    return {"user_id": new_user.id, "message": "User registered successfully"}


@app.post("/users/login")
def login(credentials: UserCredentials, user_service: UserServiceProtocol = Depends(UserService)) -> dict:

    try:
        token = user_service.login(credentials)
    # if nothing is returned the error will arise
    except UserCredentialsError:
        raise HTTPException(status_code=400, detail="Wrong email or password")
    return token


class AdRepo:
    def __init__(self, db=Depends(get_db)):
        self.db = db

    def insert_ad(self, user_id: int, ad: Ad) -> int:
        # if id exist, ad applying is carry on
        with self.db.cursor() as cursor:
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
                    ad.description, ad.city, ad.phone, datetime.now(), user_id
                )
            )
            self.db.commit()

            return cursor.fetchone()['id']

    def fetch_ad_data(self, ad_id: int | None = None, only_moderated: bool = False) -> list | dict:
        query = """
            SELECT id, vin, vrc, license_plate, brand, model, mileage, engine_capacity, price, description, city, phone, posted_at
                 FROM ads 
            """

        params = []
        conditions = []

        if ad_id is not None:
            conditions.append("id = %s")
            params.append(ad_id)

        if only_moderated:
            conditions.append("is_moderated = true")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        with self.db.cursor() as cursor:
            cursor.execute(query, params)

            if ad_id:
                item = cursor.fetchone()
            else:
                item = cursor.fetchall()

        return item

    def moderate(self, item_id: int) -> None:
        with self.db.cursor() as cursor:
            cursor.execute(
                """
                UPDATE ads SET is_moderated = true
                WHERE id = %s 
                """,
                [item_id]
            )

            self.db.commit()


class AdRepoProtocol(Protocol):
    def insert_ad(self, user_id: int, ad: Ad) -> int:
        pass

    def fetch_ad_data(self, ad_id: int | None, only_moderated: bool = False) -> list | dict:
        pass

    def moderate(self, item_id: int) -> None:
        pass


class AdService:

    def __init__(self, ad_repo: AdRepoProtocol = Depends(AdRepo)):
        self.ad_repo = ad_repo

    def add_ad(self, user_id: int | None, ad: Ad) -> int:

        if user_id is None:
            raise UserRequiredError()

        return self.ad_repo.insert_ad(user_id, ad)

    def read_ads(self, ad_id: int | None = None, only_moderated: bool = False) -> list | dict:

        items = self.ad_repo.fetch_ad_data(ad_id, only_moderated)

        if items is None:
            raise ItemRequiredError()

        return items

    def moderate(self, user: User | None, item_id: int) -> None:

        if not user:
            raise UserRequiredError("User is required")

        if not user.is_admin:
            raise PermissionError("Insufficient access rights")

        # fetching the item from db according item_id ID
        item = self.ad_repo.fetch_ad_data(item_id)

        if item is None:
            raise ItemRequiredError()

        # getting ID from item which was received according ID for moderation
        ad_id = item["id"]

        self.ad_repo.moderate(ad_id)


class AdServiceProtocol(Protocol):
    def add_ad(self, user_id: int | None, ad: Ad) -> int:
        pass

    def moderate(self, user: User | None, item_id: int | None) -> None:
        pass

    def read_ads(self, ad_id: int | None = None, only_moderated: bool = False) -> dict | list:
        pass


@app.post("/ads")
def add_ad(ad: Ad, request: Request, ad_service: AdServiceProtocol = Depends(AdService)) -> dict:
    user_id = getattr(request.state.user, 'id', None)

    try:
        ad_id = ad_service.add_ad(user_id, ad)
    except UserRequiredError:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return {"message": "Ad applied successfully", "id": ad_id}


@app.get("/ads")
def read_ads(ad_service: AdServiceProtocol = Depends(AdService)) -> list:
    items = ad_service.read_ads(only_moderated=True)

    return items


@app.get("/ads/{item_id}")
def read_ad(item_id, ad_service: AdServiceProtocol = Depends(AdService)) -> dict:
    try:
        item = ad_service.read_ads(item_id, only_moderated=True)
    except ItemRequiredError:
        raise HTTPException(status_code=404, detail="Item not found")

    return item


@app.post("/ads/{item_id}/moderate")
def moderate(item_id: int, request: Request, ad_service: AdServiceProtocol = Depends(AdService)) -> dict:
    user = getattr(request.state, 'user', None)

    try:
        ad_service.moderate(user, item_id)
    except UserRequiredError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Forbidden")
    except ItemRequiredError:
        raise HTTPException(status_code=404, detail="Item not found")
    else:
        return {"message": "moderation_completed"}
