from typing import Optional
from pydantic import BaseModel, EmailStr

class ProductSchema(BaseModel):
    title: str
    description: str | None = None
    at_sale: bool = False
    inventory: int
    added_at: str


class User(BaseModel):
    username: str
    email: str
    full_name: str | None = None
    status: bool | None = True

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None