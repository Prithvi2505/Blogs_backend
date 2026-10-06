from pydantic import BaseModel
from typing import Literal


UserRole = Literal["reader", "author", "admin"]


class UserCreate(BaseModel):
	name: str
	email: str
	password: str
	role: Literal["reader", "author"]


class UserLogin(BaseModel):
	email: str
	password: str
