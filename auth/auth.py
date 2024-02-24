import os
import secrets
import random
import json
import requests
import aiofiles
import redis
from sqlalchemy import update

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from fastapi import Depends, APIRouter, HTTPException,status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

from .utils import generate_token, verify_token
from database import get_async_session
from sqlalchemy import select, insert, update
from fastapi import APIRouter, UploadFile

from .schemes import UserRegister, UserInDB, UserInfo, UserLogin, UserUpdate
from models.models import users

from datetime import datetime
from pydantic import EmailStr
from config import GOOGLE_CLIENT_ID, GOOGLE_REDIRECT_URL, GOOGLE_CLIENT_SECRET_KEY, REDIS_HOST, REDIS_PORT
from tasks import send_mail_for_forget_password

from dotenv import load_dotenv


load_dotenv()
redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
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



@register_router.get('/forget-password/{email}')
async def forget_password(
        email: EmailStr,
        session: AsyncSession = Depends(get_async_session)
):
    try:
        user = select(users).where(users.c.email == email)
        user_data = await session.execute(user)
        if user_data.fetchone() is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Invalid Email address")

        code = random.randint(99999, 999999)
        redis_client.set(f'{email}', json.dumps({'code': code}))
        send_mail_for_forget_password.delay(email, code)
        return {"detail": "Check your email"}
    except Exception as e:
        raise HTTPException(detail=f'{e}', status_code=status.HTTP_400_BAD_REQUEST)


@register_router.post('/reset-password/{email}')
async def reset_password(
        email: str,
        code: int,
        new_password: str,
        confirm_password: str,
        session: AsyncSession = Depends(get_async_session)
):

    try:
        if new_password != confirm_password:
            raise HTTPException(detail="Passwords do not match!", status_code=status.HTTP_400_BAD_REQUEST)

        data = redis_client.get(email)
        js_data = json.loads(data)

        if js_data['code'] == code:
            query = update(users).where(users.c.email == email).values({users.c.password: pwd_context.hash(new_password)})
            await session.execute(query)
            await session.commit()

            return {"detail": "Password changed successfully"}
    except Exception as e:
        raise HTTPException(detail=f'{e}', status_code=status.HTTP_400_BAD_REQUEST)

