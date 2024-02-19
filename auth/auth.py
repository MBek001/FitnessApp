import secrets
import random
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import NoResultFound
from fastapi import Depends, APIRouter, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

from .utils import generate_token, verify_token
from database import get_async_session
from sqlalchemy import select, insert
from fastapi import APIRouter
from database import async_session_maker
from .schemes import UserRegister, UserInDB, UserInfo, UserLogin
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
        user_info = UserInfo(**dict(user_in_db))
        return dict(user_info)
    else:
        raise HTTPException(status_code=400, detail='Passwords are not the same !')


@register_router.post('/login')
async def login(user: UserLogin, session: AsyncSession = Depends(get_async_session)):
    query = select(users).where(users.c.email == user.email)
    userdata = await session.execute(query)
    user_data = userdata.one()
    if pwd_context.verify(user.password, user_data.password):
        token = generate_token(user_data.id)
        return token
    else:
        return {'success': False, 'message': 'Username or password is not correct!'}


# @register_router.get('/forgot_password{email}')
# async def forgot_pass(
#         email: str,
#         session: AsyncSession = Depends(get_async_session)
# ):
#     try:
#         user = select(users).where(users.c.email == email)
#         user_data = await session.execute(user)
#         if user_data.fetchone() is None:
#             raise HTTPException(status_code=400, detail="Invalid Email address")
#

async def is_admin(token: dict = Depends(verify_token), session: AsyncSession = Depends(get_async_session)):
    admin_id = token['user_id']
    query = select(users).where(users.c.id == admin_id)
    query = await session.execute(query)
    query = query.one()
    await session.close()
    if query[-1] == 'admin':
        return {'is_admin': True}
    else:
        return {'is_admin': False}
