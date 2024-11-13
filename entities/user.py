from pydantic import BaseModel, EmailStr


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
