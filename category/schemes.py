import datetime
from enum import Enum
from pydantic import BaseModel


class LevelEnum(str, Enum):
    beginner = 'beginner',
    intermediate = 'intermediate',
    advanced = 'advanced',


class Category(BaseModel):
    name: str
    level_id: int


class GetCategory(BaseModel):
    id: int
    name: str
    level_id: int
    photo_url: str


class Exercises(BaseModel):
    name: str
    category_id: int
    instruction: str


class GetExercises(BaseModel):
    id: int
    name: str
    category_id: int
    video_url: str
    instruction: str

class Level(BaseModel):
    name: LevelEnum


class GetLevel(BaseModel):
    id: int
    name: str
