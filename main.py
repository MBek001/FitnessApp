import os
from datetime import datetime, date, timedelta
from typing import List, Union

import aiofiles
import secrets
from fastapi import FastAPI, Depends, HTTPException, APIRouter, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, update, func, join
from starlette.responses import JSONResponse

from auth.utils import verify_token
from database import get_async_session
from scheme import *
from models.models import *

from auth.auth import register_router


app = FastAPI(title='FitnessApp', version='1.0.0')
router = APIRouter()


@router.get('/')
async def homepage(token: dict = Depends(verify_token),
                   session: AsyncSession = Depends(get_async_session)):
    if token is None:
        raise HTTPException(status_code=403, detail='Forbidden')

    user_id = token.get('user_id')

    user_data = await session.execute(select(users).filter(users.c.id == user_id))
    user = user_data.all()

    query = select(workout_plan.c.minutes, workout_plan.c.calories, exercises.c.name) \
        .select_from(join(workout_plan, exercises, workout_plan.c.exercise == exercises.c.id)) \
        .where(workout_plan.c.user_id == user_id)
    workout_plans = await session.execute(query)
    user_workout_plans = workout_plans.all()

    workout_categori = await session.execute(select(workout_categories).filter(workout_categories.c.user_id == user_id))
    user_workout_categoriess = workout_categori.all()

    threedays = datetime.now() - timedelta(days=1)
    new_workouts = await session.execute(select(exercises).where(exercises.c.date_added >= threedays))
    new_workouts = new_workouts.all()

    user_dict = []
    for u in user:
        udict = {
            'name': u.name,
        }
        user_dict.append(udict)

    plan_dict = []
    for p in user_workout_plans:
        pdict = {
            'minutes': p.minutes,
            'calories': p.calories,
            'exercise': p.name,
        }
        plan_dict.append(pdict)

    new_workouts_formatted = []
    for workout in new_workouts:
        new_workout_dict = {
            "name": workout.name,
            "instruction": workout.instruction,

        }
        new_workouts_formatted.append(new_workout_dict)

    category = []
    for cate in user_workout_categoriess:
        cate_dict = {
            "category": cate.category,
        }
        category.append(cate_dict)

    return {
            "User": user_dict,
            "Workout Plan": plan_dict,
            "New Workouts": new_workouts_formatted,
            "Categories": category
             }


app.include_router(register_router, prefix='/auth')
app.include_router(router, prefix='/main')
