import json
import redis
from typing import List
from sqlalchemy import func, insert, delete
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from auth.utils import verify_token
from database import get_async_session
from sqlalchemy import select
from fastapi import APIRouter
from .schemes import *
from starlette import status


from models.models import *

trainer_router = APIRouter()
r = redis.Redis(host='redis', port=6379, db=0)


@trainer_router.post("/add_trainers")
async def add_trainer(
        user_id: int,
        expirence: int,
        phone_number: str,
        description: str,
        cost: float,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)):
    if token is None:
        raise HTTPException(status_code=403, detail='Forbidden')

    user_idd = token.get('user_id')
    result = await session.execute(
        select(users).where(
            (users.c.id == user_idd) &
            (users.c.is_admin == True)
        )
    )
    quer = await session.execute(
        select(trainer).where(
            (trainer.c.user_id == user_id)
        )
    )
    if result.scalar():
        if not quer.scalar():
            query = insert(trainer).values(
                experience=expirence,
                cost=cost,
                phone_number=phone_number,
                description=description,
                user_id=user_id
            )
            await session.execute(query)
            await session.execute(
                users.update()
                .where(users.c.id == user_id)
                .values(
                    is_trainer=True
                )
            )
            await session.commit()
            return {'success': True, 'detail': 'Trainer added successfully'}
        else:
            return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Trainer already exists')
    else:
        return HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)


@trainer_router.delete("/delete_trainers")
async def delete_trainer(
        user_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=403, detail='Forbidden')

    user_idd = token.get('user_id')
    result = await session.execute(
        select(users).where(
            (users.c.id == user_idd) &
            (users.c.is_admin == True)
        )
    )
    quer = await session.execute(
        select(trainer).where(
            (trainer.c.user_id == user_id)
        )
    )
    if result.scalar():
        if quer.scalar():
            await session.execute(
                delete(trainer).where(trainer.c.user_id == user_id)
            )
            await session.execute(
                users.update()
                .where(users.c.id == user_id)
                .values(
                    is_trainer=False
                )
            )
            await session.commit()
            return {'success': True, 'detail': 'Trainer deleted successfully'}
        else:
            return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Trainer not found')
    else:
        return HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)


@trainer_router.get("/check-trainer-availability", response_model=List[str])
async def check_trainer_availability(trainer_id: int, date: str,
                                     session: AsyncSession = Depends(get_async_session),
                                     token: dict = Depends(verify_token)):
    if token is None:
        raise HTTPException(status_code=403, detail='Forbidden')

    is_trainer = select(trainer.c.id).where(trainer.c.id == trainer_id)
    iss_trainer = await session.execute(is_trainer)
    if not iss_trainer.scalar():
        raise HTTPException(status_code=404, detail='Trainer not found')

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
    booked_slots = result.scalars().all()

    free_time = [
        taym.strftime("%H:%M")
        for taym in available_time
        if taym not in booked_slots
    ]

    return free_time


@trainer_router.get("/book_trainer", response_model=str)
async def book_trainer(trainer_id: int, date: str, hour: int, minute: int,
                       session: AsyncSession = Depends(get_async_session),
                       token: dict = Depends(verify_token)):
    if token is None:
        raise HTTPException(status_code=403, detail='Forbidden')

    is_trainer = select(trainer.c.id).where(trainer.c.id == trainer_id)
    iss_trainer = await session.execute(is_trainer)
    if not iss_trainer.scalar():
        raise HTTPException(status_code=404, detail='Trainer not found')

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
        data = {
            'date': date,
            'hours': hour,
            'minutes': minute
        }
        r.set('datetime', json.dumps(data))

        return "Doda Pizza"

    else:
        return " Trainer is not available at the selected time."


@trainer_router.get("/trainer-info")
async def get_trainer_detail(
        trainer_id: int,
        session: AsyncSession = Depends(get_async_session)
):
    result = select(trainer).join(users, trainer.c.user_id == users.c.id).filter(
        trainer.c.id == trainer_id).with_only_columns(
        trainer.c.id,
        trainer.c.user_id,
        users.c.name,
        trainer.c.experience,
        trainer.c.completed,
        trainer.c.active_clients,
        trainer.c.phone_number,
        trainer.c.description
    )
    data = await session.execute(result)
    trainer_data = data.fetchone()
    if trainer_data is None:
        raise HTTPException(status_code=404, detail="Trainer not found")

    return TrainerDetailResponse(
        trainer_id=trainer_data.id,
        user_id=trainer_data.user_id,
        name=trainer_data.name,
        experience=trainer_data.experience,
        active_clients=trainer_data.active_clients,
        phone_number=trainer_data.phone_number,
        description=trainer_data.description
    )


@trainer_router.get('/all_trainers_info', response_model=List[Trainers])
async def trainer_(token: dict = Depends(verify_token),
                   session: AsyncSession = Depends(get_async_session)):
    try:
        if token:
            all_trainer = []
            query = select(users).where(users.c.is_trainer)
            blog_date = await session.execute(query)
            await session.execute(query)
            query = blog_date.fetchall()
            is_trainer = select(trainer)
            is_trainer = await session.execute(is_trainer)
            is_trainer = is_trainer.fetchall()
            view = len(is_trainer)
            for i in range(0, view):
                if is_trainer[i][-2]:
                    data = {
                        "name": query[i][1],
                        "experience": is_trainer[i][2],
                        "rate": is_trainer[i][-2],
                        "description": is_trainer[i][-1]
                    }
                    all_trainer.append(data)
                else:
                    data = {
                        "name": query[i][1],
                        "experience": is_trainer[i][2],
                        "rate": 0,
                        "description": is_trainer[i][-1]
                    }
                    all_trainer.append(data)
            return all_trainer
    except Exception as e:
        return {"success": False, "message": f"{e}"}
