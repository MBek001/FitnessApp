from pydantic import BaseModel
from typing import Optional
from enum import Enum
from datetime import datetime
from models.models import GenderEnum, GoalEnum, CategoryEnum, ActivityEnum, SubDurationEnum, StatusEnum, LanguageEnum, WeekdaysEnum, BookDurationEnum


class UserModel(BaseModel):
    name: str
    photo_url: Optional[str]
    password: str
    email: str
    age: int
    weight: int
    height: int
    gender: GenderEnum
    is_trainer: Optional[bool] = False
    user_role: Optional[str]


class UserGoalModel(BaseModel):
    goal: GoalEnum
    activity: ActivityEnum


class WorkoutCategoryModel(BaseModel):
    category: CategoryEnum


class ExerciseModel(BaseModel):
    name: str
    video_url: Optional[str]
    instruction: str


class SubscriptionModel(BaseModel):
    purchase_name: str
    monthly_fee: float
    yearly_fee: float


class UserSubscriptionModel(BaseModel):
    duration: SubDurationEnum
    created_at: Optional[datetime]


class UserStatusModel(BaseModel):
    status: StatusEnum


class TrainerModel(BaseModel):
    experience: int
    completed: int
    active_clients: int
    phone_number: str
    rate: float
    description: str


class ReviewModel(BaseModel):
    rating: int
    comment: str


class SavedCardModel(BaseModel):
    card_holder_name: str
    card_number: str
    expiry_month: int


class LanguageModel(BaseModel):
    language: LanguageEnum


class BookedTrainerModel(BaseModel):
    date: datetime
    duration: BookDurationEnum


class InsightsModel(BaseModel):
    calories: float
    steps: int
    time_spent: float
    heartbeat: int
    day: WeekdaysEnum
    date: datetime


class WorkoutPlanModel(BaseModel):
    minutes: int
    calories: int



