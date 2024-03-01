from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from auth.utils import verify_token
from database import get_async_session
from sqlalchemy import select
from fastapi import APIRouter
from .schemes import Trainers

from models.models import users, trainer

trainer_router = APIRouter()


@trainer_router.get('/fitness_instructions', response_model=List[Trainers])
async def trainer_(token: dict = Depends(verify_token),
                   session: AsyncSession = Depends(get_async_session)):
    try:
        if token:
            all_trainer = []
            query = select(users).where(users.c.is_trainer)
            blog_date = await session.execute(query)
            await session.execute(query)
            query = blog_date.fetchall()
            is_trainer = select(trainer)
            is_trainer = await session.execute(is_trainer)
            is_trainer = is_trainer.fetchall()
            view = len(is_trainer)
            for i in range(0, view):
                data = {
                    "name": query[i][1],
                    "experience": is_trainer[i][2],
                    "rate": is_trainer[i][-2],
                    "description": is_trainer[i][-1]
                }
                all_trainer.append(data)
            return all_trainer
    except Exception as e:
        return {"success": False, "message": f"{e}"}
