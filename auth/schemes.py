from enum import Enum
from pydantic import BaseModel


class GenderEnum(str, Enum):
    male = 'male'
    female = 'female'


class UserRegister(BaseModel):
    name: str
    email: str
    password1: str
    password2: str
    age: int
    weight: int
    height: int
    gender: GenderEnum


class UserInDB(BaseModel):
    name: str
    email: str
    password: str
    age: int
    weight: int
    height: int


class UserInfo(BaseModel):
    name: str
    email: str
    age: int
    weight: int
    height: int


class UserLogin(BaseModel):
    email: str
    password: str
