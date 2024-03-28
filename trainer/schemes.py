from pydantic import BaseModel


class Trainers(BaseModel):
    id: int
    user_id: int
    name: str
    experience: int
    rate: float
    description: str


class TrainerDetailResponse(BaseModel):
    name: str
    experience: int
    active_clients: int
    phone_number: str
    description: str
