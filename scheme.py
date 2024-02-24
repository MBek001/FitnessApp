import enum

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from models.models import (GenderEnum, GoalEnum, CategoryEnum, ActivityEnum, SubDurationEnum, StatusEnum, LanguageEnum,
                           WeekdaysEnum)



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


class ReviewData(BaseModel):
    trainer_id: int
    user_id: int
    rating: int
    comment: str


class TrainerAvailable(BaseModel):
    trainer_id: int
    date: datetime
    hour: int
    minutes: int


class BookDurationEnumScheme(enum.Enum):
    half_hour: int
    one_hour: int
    two_hours: int
