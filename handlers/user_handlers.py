from typing import Protocol
from entities.user import UserCreate, User, UserCredentials
from fastapi import Depends, HTTPException
from services.user_service import UserService
from errors import UserCredentialsError


class UserServiceProtocol(Protocol):

    def make_user(self, user: UserCreate) -> User:
        pass

    def login(self, credentials: UserCredentials) -> dict | None:
        pass


# @app.post("/users/registration")
def registration(user: UserCreate, user_service: UserServiceProtocol = Depends(UserService)) -> dict:
    new_user = user_service.make_user(user)

    return {"user_id": new_user.id, "message": "User registered successfully"}


# @app.post("/users/login")
def login(credentials: UserCredentials, user_service: UserServiceProtocol = Depends(UserService)) -> dict:

    try:
        token = user_service.login(credentials)
    # if nothing is returned the error will arise
    except UserCredentialsError:
        raise HTTPException(status_code=400, detail="Wrong email or password")
    return token