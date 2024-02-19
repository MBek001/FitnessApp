from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from auth.auth import is_admin
from auth.utils import verify_token
from database import get_async_session
from sqlalchemy import select, insert
from fastapi import APIRouter
from models.models import users, workout_categories, exercises, category
from .schemes import WorkoutCategory, Category, GetCategory, Exercises, GetExercises

category_router = APIRouter()


@category_router.post('/workout_categories')
async def login(blog: WorkoutCategory, session: AsyncSession = Depends(get_async_session),
                token: dict = Depends(verify_token)):
    user_id = token['user_id']
    if token:
        query = insert(workout_categories).values(user_id=int(user_id), category=dict(blog)['category'])
        await session.execute(query)
        await session.commit()
        data = dict(blog)
        return {'success': True, 'message': 'Category added!', 'data': data}


@category_router.get('/workout_categories')
async def getting(token: dict = Depends(verify_token), session: AsyncSession = Depends(get_async_session)):
    user_id = token['user_id']
    if token:
        query = select(workout_categories).where(workout_categories.c.id == user_id)
        query = await session.execute(query)
        query = query.one()
        return {"id": query.id, "user_id": query.user_id, "category_name": query.category}


@category_router.post('/category')
async def category_(blog: Category, token: dict = Depends(verify_token),
                    session: AsyncSession = Depends(get_async_session)):
    if token and await is_admin(token, session):
        query = insert(category).values(**dict(blog))
        await session.execute(query)
        await session.commit()
        return {'success': True, 'data': blog}


@category_router.get('/category', response_model=List[GetCategory])
async def category_(token: dict = Depends(verify_token), session: AsyncSession = Depends(get_async_session)):
    if token and await is_admin(token, session):
        query = select(category)
        query = await session.execute(query)
        query_ = query.all()
        return query_


@category_router.post('add-exercises')
async def exercises_(blog: Exercises, token: dict = Depends(verify_token),
                     session: AsyncSession = Depends(get_async_session)):
    if token and await is_admin(token, session):
        query = insert(exercises).values(**dict(blog))
        await session.execute(query)
        await session.commit()
        return {'success': True, 'message': 'Exercises added!'}


@category_router.get('/exercises', response_model=List[GetExercises])
async def get_exercises(token: dict = Depends(verify_token),
                        session: AsyncSession = Depends(get_async_session)):
    if token and await is_admin(token, session):
        query = select(exercises)
        query = await session.execute(query)
        await session.close()
        return query
