from pydantic import BaseModel


class Trainers(BaseModel):
    id: int
    user_id: int
    name: str
    experience: int
    rate: float
    description: str
