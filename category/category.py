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

from models.models import user_level
from scheme import UserWorkout

from models.models import exercises, category, level
from .schemes import Category, GetCategory, Exercises, GetExercises, Level, GetLevel


category_router = APIRouter()


@category_router.post('/user_workout')
async def login(blog: UserWorkout, session: AsyncSession = Depends(get_async_session),
                token: dict = Depends(verify_token)):
    try:
        user_id = token['user_id']
        if token:
            query = insert(user_level).values(user_id=int(user_id), level_id=int(dict(blog)['level_id']))
            await session.execute(query)
            await session.commit()
            return {"success": True, "message": "Workout Category added!"}
    except Exception as e:
        return {"success": False, "message": f"{e}"}


@category_router.get('/user_workout_information', response_model=dict)
async def getting(token: dict = Depends(verify_token), session: AsyncSession = Depends(get_async_session)):
    try:
        user_id = token['user_id']
        if token:
            query = select(user_level).where(user_level.c.user_id == user_id)
            query = await session.execute(query)
            query = query.fetchone()
            data = {
                "id": query[0],
                "user_id": query[1],
                "level_id": query[2]
            }
            return {"success": True, "data": data}
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
            query = insert(category).values(photo_url=f'category_photos/{out_file}', level_id=level_id,
                                            name=name)
            await session.execute(query)
            await session.commit()
        return {"success": True, "data": "Category added!"}
    except Exception as e:
        return {"success": False, "message": f"{e}"}


@category_router.get('/category_info', response_model=List[GetCategory])
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
async def exercises_(video: UploadFile, instruction: str, name: str,level_id:int, category_id: int,
                     token: dict = Depends(verify_token),
                     session: AsyncSession = Depends(get_async_session)):
    try:
        if token and await is_admin(token, session) and video:
            if video and token and await is_admin(token, session):
                out_file = f'{video.filename}'
                async with aiofiles.open(f'exercises_videos/{out_file}', 'wb') as f:
                    content = await video.read()
                    await f.write(content)
                query = insert(exercises).values(level_id=level_id,
                                                 category_id=category_id,
                                                 name=name,
                                                 video_url=f'exercises_videos/{out_file}',
                                                 instruction=instruction)
                await session.execute(query)
                await session.commit()
                return {'success': True, 'message': 'Exercises added!'}
    except Exception as e:
        return {"success": False, "message": f"{e}"}


@category_router.get('/exercises_info', response_model=List[GetExercises])
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
