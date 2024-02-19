from enum import Enum
from pydantic import BaseModel


class CategoryEnum(str, Enum):
    beginner = 'beginner',
    intermediate = 'intermediate',
    advanced = 'advanced',


class WorkoutCategory(BaseModel):
    category: CategoryEnum


class Category(BaseModel):
    name: str


class GetCategory(BaseModel):
    id: int
    name: str


class Exercises(BaseModel):
    name: str
    category_id: int


class GetExercises(BaseModel):
    id: int
    name: str
    category_id: int
