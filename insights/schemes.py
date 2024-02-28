import datetime
from enum import Enum
from pydantic import BaseModel


class WeekdaysEnum(str, Enum):
    monday = 'monday',
    tuesday = 'tuesday',
    wednesday = 'wednesday',
    thursday = 'thursday',
    friday = 'friday',
    saturday = 'saturday',
    sunday = 'sunday',


class InsightsPost(BaseModel):
    calories: float
    steps: int
    time_spent: float
    heartbeat: int
    day: WeekdaysEnum
    date: datetime.date


class GetInsightsPost(BaseModel):
    id: int
    calories: float
    steps: int
    time_spent: float
    heartbeat: int
    day: str
    date: datetime.date
