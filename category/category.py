import secrets
from typing import List

import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, UploadFile
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
async def category_(photo: UploadFile, level_id: int, name: str, token: dict = Depends(verify_token),
                    session: AsyncSession = Depends(get_async_session)):
    try:
        if photo and token and await is_admin(token, session):
            out_file = f'{photo.filename}'
            async with aiofiles.open(f'category_photos/{out_file}', 'wb') as f:
                content = await photo.read()
                await f.write(content)
            photo_hashcode = secrets.token_hex(32)
            query = insert(category).values(photo_url=f'category_photos/{out_file}', level_id=level_id,
                                            name=name,
                                            photo_hashcode=photo_hashcode)
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
            query = query.fetchall()
            return query
    except Exception as e:
        return {"success": False, "message": f"{e}"}


@category_router.post('/add_exercises')
async def exercises_(video: UploadFile, instruction: str, name: str, category_id: int,
                     token: dict = Depends(verify_token),
                     session: AsyncSession = Depends(get_async_session)):
    try:
        if token and await is_admin(token, session) and video:
            if video and token and await is_admin(token, session):
                out_file = f'/{video.filename}'
                async with aiofiles.open(f'exercises_videos/{out_file}', 'wb') as f:
                    content = await video.read()
                    await f.write(content)
                video_hashcode = secrets.token_hex(32)
                query = insert(exercises).values(category_id=category_id, name=name,
                                                 video_url=f'exercises_videos/{out_file}',
                                                 video_hashcode=video_hashcode, instruction=instruction)
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
            query = query.fetchall()
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


@category_router.get('/levels', response_model=list[GetLevel])
async def lev(token: dict = Depends(verify_token),
              session: AsyncSession = Depends(get_async_session)):
    try:
        if token and await is_admin(token, session):
            query = select(level)
            query = await session.execute(query)
            query = query.fetchall()
            return query
    except Exception as e:
        return {"success": False, "message": f"{e}"}
