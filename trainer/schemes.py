from pydantic import BaseModel


class Trainers(BaseModel):
    name: str
    experience: int
    rate: float
    description: str
