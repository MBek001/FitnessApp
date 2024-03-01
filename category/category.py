from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from auth.auth import is_admin
from auth.utils import verify_token
from database import get_async_session
from sqlalchemy import select, insert
from fastapi import APIRouter
from models.models import workout_categories, exercises, category, level
from .schemes import WorkoutCategory, Category, GetCategory, Exercises, GetExercises, Level, GetLevel

category_router = APIRouter()


@category_router.post('/user_workout')
async def login(blog: WorkoutCategory, session: AsyncSession = Depends(get_async_session),
                token: dict = Depends(verify_token)):
    try:
        user_id = token['user_id']
        if token:
            query = insert(workout_categories).values(user_id=int(user_id), level_id=int(dict(blog)['level_id']))
            await session.execute(query)
            await session.commit()
            return {"success": True, "message": "Workout Category added!"}
    except Exception as e:
        return {"success": False, "message": f"{e}"}


@category_router.get('/user_workout_information')
async def getting(token: dict = Depends(verify_token), session: AsyncSession = Depends(get_async_session)):
    try:
        user_id = token['user_id']
        if token:
            query = select(workout_categories).where(workout_categories.c.user_id == user_id)
            query = await session.execute(query)
            query = query.fetchone()
            return query
    except Exception as e:
        return {"success": True, "message": f"{e}"}


@category_router.post('/add_category')
async def category_(blog: Category, token: dict = Depends(verify_token),
                    session: AsyncSession = Depends(get_async_session)):
    try:
        if token and await is_admin(token, session):
            query = insert(category).values(**dict(blog))
            await session.execute(query)
            await session.commit()
            return {"success": True, "data": "Category added!"}
    except Exception as e:
        return {"success": False, "message": f"{e}"}


@category_router.get('/categories', response_model=List[GetCategory])
async def category_(token: dict = Depends(verify_token), session: AsyncSession = Depends(get_async_session)):
    try:
        if token and await is_admin(token, session):
            query = select(category)
            query = await session.execute(query)
            query_ = query.all()
            return query_
    except Exception as e:
        return {"success": False, "message": f"{e}"}


@category_router.post('/add_exercises')
async def exercises_(blog: Exercises, token: dict = Depends(verify_token),
                     session: AsyncSession = Depends(get_async_session)):
    try:
        if token and await is_admin(token, session):
            query = insert(exercises).values(**dict(blog))
            await session.execute(query)
            await session.commit()
            return {'success': True, 'message': 'Exercises added!'}
    except Exception as e:
        return {"success": False, "message": f"{e}"}


@category_router.get('/exercises', response_model=List[GetExercises])
async def get_exercises(token: dict = Depends(verify_token),
                        session: AsyncSession = Depends(get_async_session)):
    try:
        if token and await is_admin(token, session):
            query = select(exercises)
            query = await session.execute(query)
            await session.close()
            return query
    except Exception as e:
        return {"success": False, "message": f"{e}"}


@category_router.post('/add_level')
async def level_(blog: Level, token: dict = Depends(verify_token),
                 session: AsyncSession = Depends(get_async_session)):
    try:
        if token and await is_admin(token, session):
            query = insert(level).values(**dict(blog))
            await session.execute(query)
            await session.commit()
            return {"success": True, "message": "Level added!"}
    except Exception as e:
        return {"success": False, "message": f"{e}"}


@category_router.get('/levels', response_model=GetLevel)
async def lev(token: dict = Depends(verify_token),
              session: AsyncSession = Depends(get_async_session)):
    try:
        if token and await is_admin(token, session):
            query = select(level)
            query = await session.execute(query)
            query = query.fetchone()
            return query
    except Exception as e:
        return {"success": False, "message": f"{e}"}
