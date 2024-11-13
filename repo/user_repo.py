from fastapi import Depends
from db import get_db
from entities.user import UserCreate, User, UserCredentials
from datetime import datetime


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
