from enum import Enum
from pydantic import BaseModel


class LevelEnum(str, Enum):
    beginner = 'beginner',
    intermediate = 'intermediate',
    advanced = 'advanced',


class WorkoutCategory(BaseModel):
    level_id: int


class Category(BaseModel):
    name: str
    photo_url: str
    level_id: int


class GetCategory(BaseModel):
    id: int
    name: str
    level_id: int
    photo_url: str


class Exercises(BaseModel):
    name: str
    category_id: int
    video_url: str
    video_hash: str
    instruction: str


class GetExercises(BaseModel):
    id: int
    name: str
    category_id: int
    video_url: str
    video_hash: str
    instruction: str

class Level(BaseModel):
    name: LevelEnum


class GetLevel(BaseModel):
    id: int
    name: str
