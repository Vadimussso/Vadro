from fastapi import FastAPI, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import psycopg2
from psycopg2.extras import RealDictCursor
from config import settings
from entities.user import User
from handlers.ad_handlers import read_ads


app = FastAPI()

auth_scheme = HTTPBearer()


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


app.add_api_route('/ads', endpoint=read_ads, methods=["GET"])






