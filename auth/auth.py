import os
import secrets
import random
import json

import aiofiles
from sqlalchemy import update

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from fastapi import Depends, APIRouter, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

from .utils import generate_token, verify_token
from database import get_async_session
from sqlalchemy import select, insert
from fastapi import APIRouter, UploadFile

from .schemes import UserRegister, UserInDB, UserInfo, UserLogin, UserUpdate
from models.models import users

register_router = APIRouter()
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')




@register_router.post('/register')
async def register(
        user_data: UserRegister,
        session: AsyncSession = Depends(get_async_session)
):
    if user_data.password1 == user_data.password2:

        email_exists = await session.execute(select(users).where(users.c.email == user_data.email))
        email_exists_value = email_exists.scalar()

        if email_exists_value is not None:
            return {'success': False, 'message': 'Email already exists!'}

        if user_data.age <= 0 and user_data.weight <= 0 and user_data.height <= 0:
            return {'success': False, 'message': 'Enter correct number!'}

        hash_password = pwd_context.hash(user_data.password1)
        user_in_db = UserInDB(**dict(user_data), password=hash_password)
        query = insert(users).values(**dict(user_in_db))
        await session.execute(query)
        await session.commit()
        return {'success': True, 'message':'Account created successfully'}
    else:
        raise HTTPException(status_code=400, detail='Passwords are not the same !')


@register_router.post('/login')
async def login(user: UserLogin, session: AsyncSession = Depends(get_async_session)):
    query = select(users).where(users.c.email == user.email)
    userdata = await session.execute(query)
    user_data = userdata.one_or_none()
    if user_data is None:
        return {'success': False, 'message': 'Email or password is not correct!'}
    else:
        if pwd_context.verify(user.password, user_data.password):
            token = generate_token(user_data.id)
            return token
        else:
            return {'success': False, 'message': 'Email or password is not correct!'}




@register_router.patch('/edit-profile')
async def edit_profile(
        photo: UploadFile,
        name: str,
        email: str,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    if token is None:
        return HTTPException(status_code=403, detail='Forbidden')
    try:
        user_id = token.get('user_id')
        query = select(users).where(users.c.id == user_id)
        userdata = await session.execute(query)
        user_data = userdata.one_or_none()
        out_file = f'/{photo.filename}'
        async with aiofiles.open(f'user_photos/{out_file}', 'wb') as f:
            content = await photo.read()
            await f.write(content)

        query = update(users).where(users.c.id == user_data.id).values(
            email=email,
            name=name,
            photo_url=out_file
        )
        await session.execute(query)
        await session.commit()
    except Exception as e:
        raise HTTPException(status_code=400, detail=e)
    return {'success': True, 'message': 'Profile updated successfully!'}





