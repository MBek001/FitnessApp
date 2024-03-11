from pydantic import BaseModel


class UserWorkout(BaseModel):
    level_id: int

