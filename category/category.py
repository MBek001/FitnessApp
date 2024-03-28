import secrets
from typing import List

import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, UploadFile, HTTPException
from starlette import status

from auth.utils import verify_token
from database import get_async_session
from sqlalchemy import select, insert, delete
from fastapi import APIRouter

from models.models import user_level, users
from scheme import UserWorkout

from models.models import exercises, category, level
from .schemes import Category, GetCategory, Exercises, GetExercises, Level, GetLevel

category_router = APIRouter()


@category_router.post('/add_level')
async def level_(blog: Level, token: dict = Depends(verify_token),
                 session: AsyncSession = Depends(get_async_session)):
    user_id = token.get('user_id')
    result = await session.execute(
        select(users).where(
            (users.c.id == user_id) &
            (users.c.is_admin == True)
        )
    )
    if token is None:
        raise HTTPException(status_code=403, detail='Forbidden')

    if not result.scalar():
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)

    name = f"{blog.name}".split('.')[1]
    query1 = select(level).where(level.c.name == name)
    query1 = await session.execute(query1)
    query1 = query1.fetchone()

    try:
        if not query1:
            query = insert(level).values(**dict(blog))
            await session.execute(query)
            await session.commit()
            return {"success": True, "message": "Level added!"}
        else:
            return {"success": True, "message": "Level already exist!"}
    except Exception as e:
        return {"success": False, "message": f"{e}"}


@category_router.get('/levels_info', response_model=list[GetLevel])
async def lev(token: dict = Depends(verify_token),
              session: AsyncSession = Depends(get_async_session)):
    try:
        if token:
            query = select(level)
            query = await session.execute(query)
            query = query.fetchall()
            return query
    except Exception as e:
        return {"success": False, "message": f"{e}"}


@category_router.post('/add_category')
async def category_(photo: UploadFile, level_id: int, name: str, token: dict = Depends(verify_token),
                    session: AsyncSession = Depends(get_async_session)):
    user_id = token.get('user_id')
    result = await session.execute(
        select(users).where(
            (users.c.id == user_id) &
            (users.c.is_admin == True)
        )
    )
    if token is None:
        raise HTTPException(status_code=403, detail='Forbidden')

    if not result.scalar():
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
    try:
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


@category_router.get('/categories_info', response_model=List[GetCategory])
async def category_(token: dict = Depends(verify_token), session: AsyncSession = Depends(get_async_session)):
    try:
        if token:
            query = select(category)
            query = await session.execute(query)
            query = query.fetchall()
            return query
    except Exception as e:
        return {"success": False, "message": f"{e}"}


@category_router.delete("/delete_category")
async def delete_category(category_id: int, token: dict = Depends(verify_token),
                          session: AsyncSession = Depends(get_async_session)):
    user_id = token.get('user_id')
    result = await session.execute(
        select(users).where(
            (users.c.id == user_id) &
            (users.c.is_admin == True)
        )
    )
    if token is None:
        raise HTTPException(status_code=403, detail='Forbidden')
    if not result.scalar():
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)

    try:
        delete_query = delete(category).where(category.c.id == category_id)
        await session.execute(delete_query)
        await session.commit()
        await session.close()
        return {"success": True, "message": "Category deleted!"}
    except Exception as e:
      return {"success": False, "message": f"{e}"}


@category_router.post('/add_exercises')
async def exercises_(video: UploadFile, instruction: str, name: str, level_id: int, category_id: int,
                     token: dict = Depends(verify_token),
                     session: AsyncSession = Depends(get_async_session)):
    user_id = token.get('user_id')
    result = await session.execute(
        select(users).where(
            (users.c.id == user_id) &
            (users.c.is_admin == True)
        )
    )
    if token is None:
        raise HTTPException(status_code=403, detail='Forbidden')
    if not result.scalar():
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
    try:
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
        if token:
            query = select(exercises)
            query = await session.execute(query)
            query = query.fetchall()
            await session.close()
            return query
    except Exception as e:
        return {"success": False, "message": f"{e}"}


@category_router.delete('/delete_exercise')
async def delete_exercises(exercises_id: int, token: dict = Depends(verify_token),
                        session: AsyncSession = Depends(get_async_session)):
    try:
        user_id = token.get('user_id')
        result = await session.execute(
            select(users).where(
                (users.c.id == user_id) &
                (users.c.is_admin == True)
            )
        )
        if token is None:
            raise HTTPException(status_code=403, detail='Forbidden')
        if not result.scalar():
            raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)

        query = delete(exercises).where(exercises.c.id == exercises_id)
        await session.execute(query)
        await session.commit()
        await session.close()
        return {"success": True, "message": "Exercises deleted!"}
    except Exception as e:
        return {"success": False, "message": f"{e}"}







