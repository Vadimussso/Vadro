from repo.user_repo import UserRepo
from entities.user import UserCreate, User, UserCredentials
from typing import Protocol
from fastapi import Depends
from errors import UserCredentialsError


class UserRepoProtocol(Protocol):

    def make_user(self, user: UserCreate) -> User:
        pass

    def login(self, credentials: UserCredentials) -> dict:
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
