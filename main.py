
import os
from datetime import datetime, date, timedelta
from typing import List, Union

from models.models import trainer
from fastapi import Body

from sqlalchemy import select, insert,delete
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, update, func, join
from starlette.responses import JSONResponse

from auth.utils import verify_token
from database import get_async_session
from scheme import *
from models.models import *

from fastapi import FastAPI, APIRouter, HTTPException, Depends
from auth.auth import register_router
from models.models import review,users
from scheme import ReviewData
from database import get_async_session
from starlette import status

app = FastAPI(title='Fitnessapp', version='1.0.0')
from auth.utils import verify_token
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

def __init__(self, session):
    self.session = session


@router.post("/reviews/")
async def review_exercise(
        trainer_id: int = Body(...),
        comment: str = Body(...),
        rating: float = Body(...),
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token not provided!')
    user_id = token.get('user_id')
    try:
        if not 1 <= rating <= 5:
            raise HTTPException(detail='Rating must be between 1 and 5', status_code=status.HTTP_400_BAD_REQUEST)

        tool_existing_query = select(trainer).where(trainer.c.id == trainer_id)
        tool_result = await session.execute(tool_existing_query)
        if tool_result.scalar() is None:
            raise HTTPException(detail='Trainer not found!!!', status_code=status.HTTP_404_NOT_FOUND)

        insert_query = insert(review).values(
            user_id=user_id,
            trainer_id=trainer_id,
            comment=comment,
            rating=rating
        )
        await session.execute(insert_query)

        await session.commit()
        return {"success": True, "detail": "Comment created successfully"}
    except IntegrityError:
        raise HTTPException(detail='User already commented this tool', status_code=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        raise HTTPException(detail=f'{e}', status_code=status.HTTP_400_BAD_REQUEST)


@router.delete('/delete-review/')
async def delete_comment(comment_id: int, token: dict = Depends(verify_token), session: AsyncSession = Depends(get_async_session)):
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token not provided!')
    user_id = token.get('user_id')
    try:
        delete_query = delete(review).where(
            (review.c.id == comment_id),
            (review.c.user_id == user_id)
        )
        delete_data = await session.execute(delete_query)
        affected_rows = delete_data.rowcount
        if affected_rows == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        await session.commit()
        return {"status": status.HTTP_204_NO_CONTENT}
    except NoResultFound:
        raise HTTPException(detail='Not found!!!', status_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        raise HTTPException(detail=f'{e}', status_code=status.HTTP_400_BAD_REQUEST)


@router.get('/reviews-view/')
async def get_comment(trainer_id: int,
                      session: AsyncSession = Depends(get_async_session)):

    try:
        query = select(review.c.rating, review.c.comment, review.c.trainer_id, trainer.c.id, trainer.c.full_name, users.c.name) \
            .where(review.c.trainer_id == trainer_id, trainer.c.id == trainer_id)
        result = await session.execute(query)
        comments = result.all()

        if not comments:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comments not found")

        res = []
        overall = 0
        u = 0
        five = 0
        four = 0
        three = 0
        two = 0
        one = 0

        for i in comments:
            if i.rating is not None:
                u += 1
                overall += i.rating

        overall = overall / u if u != 0 else 0

        for i in comments:
            if i.rating is not None:
                if 1 <= i.rating < 2:
                    one += 1
                elif 2 <= i.rating < 3:
                    two += 1
                elif 3 <= i.rating < 4:
                    three += 1
                elif 4 <= i.rating < 5:
                    four += 1
                elif i.rating == 5:
                    five += 1

        dictjon = {
            'overall_rating': overall,
            'five': five,
            'four': four,
            'three': three,
            'two': two,
            'one': one,
            'ratings': u
        }
        res.append(dictjon)

        for item in comments:
            comment_dict = {
                'trainer': item.full_name,
                'user': item.name,
                'rating': item.rating,
                'comment': item.comment
            }
            res.append(comment_dict)

        return res

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/check-trainer-availability", response_model=List[str])
async def check_trainer_availability(trainer_id: int, date: str,
                                     session: AsyncSession = Depends(get_async_session),
                                     token: dict = Depends(verify_token)):
    if token is None:
        raise HTTPException(status_code=403, detail='Forbidden')

    selected_date = datetime.strptime(date, "%Y-%m-%d")
    print('select date', selected_date)

    start_time = datetime.combine(selected_date, datetime.min.time()) + timedelta(hours=9)
    end_time = datetime.combine(selected_date, datetime.min.time()) + timedelta(hours=23, minutes=30)

    available_time = []
    current_time = start_time
    while current_time < end_time:
        if current_time.time() < datetime.strptime("12:00", "%H:%M").time() or current_time.time() >= datetime.strptime(
                "14:00", "%H:%M").time():
            available_time.append(current_time)
        current_time += timedelta(minutes=30)

    query = select(booked_trainer.c.date).where(
        (booked_trainer.c.trainer_id == trainer_id) &
        (func.date(booked_trainer.c.date) == selected_date)
    )
    result = await session.execute(query)
    booked_slots =result.scalars().all()

    free_time = [
        taym.strftime("%H:%M")
        for taym in available_time
        if taym not in booked_slots
    ]

    return free_time


from fastapi import HTTPException

@router.get("/book_trainer", response_model=str)
async def book_trainer(trainer_id: int, date: str, hour: int, minute: int,
                       session: AsyncSession = Depends(get_async_session),
                       token: dict = Depends(verify_token)):
    if token is None:
        raise HTTPException(status_code=403, detail='Forbidden')

    selected_date_time = datetime.strptime(f"{date} {hour}:{minute}:00", "%Y-%m-%d %H:%M:00")

    start_time = datetime.combine(selected_date_time.date(), datetime.min.time()) + timedelta(hours=9)
    end_time = datetime.combine(selected_date_time.date(), datetime.min.time()) + timedelta(hours=23, minutes=30)

    available_time = []
    current_time = start_time
    while current_time < end_time:
        if current_time.time() < datetime.strptime("12:00", "%H:%M").time() or current_time.time() >= datetime.strptime(
                "14:00", "%H:%M").time():
            available_time.append(current_time)
        current_time += timedelta(minutes=30)

    query = select(booked_trainer.c.date).where(
        (booked_trainer.c.trainer_id == trainer_id) &
        (func.date(booked_trainer.c.date) == selected_date_time.date())
    )
    result = await session.execute(query)
    booked_slots = result.scalars().all()

    free_time = [
        taym.strftime("%H:%M")
        for taym in available_time
        if taym not in booked_slots
    ]
    count = False
    for i in free_time:
        if selected_date_time.time().strftime("%H:%M") == i:
            count = True

    if count:
        return " Trainer is available at the selected time."
    else:
        return " Trainer is not available at the selected time."


app.include_router(register_router, prefix='/auth')
app.include_router(router, prefix='/main')
