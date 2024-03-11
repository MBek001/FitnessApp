import json
import redis
from typing import List
from sqlalchemy import insert, select, update, func, join, delete
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from auth.utils import verify_token
from database import get_async_session
from sqlalchemy import select
from fastapi import APIRouter
from starlette import status
from models.models import *

r = redis.Redis(host='redis', port=6379, db=0)

payment_router = APIRouter()


@payment_router.get('/get-cards')
async def get_cards(
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        return HTTPException(status_code=403, detail='Forbidden')
    user_id = token.get('user_id')
    query = select(saved_cards).where(saved_cards.c.user_id == user_id)
    data = await session.execute(query)
    user_data = data.fetchall()
    if user_data is None:
        return HTTPException(status_code=404)

    cards = []
    for item in user_data:
        card = {
            'Holder Name': item.card_holder_name,
            'Card Number': item.card_number,
            'Balance': item.balance,
            'Expiry Month': item.expiry_month,
        }
        cards.append(card)

    return cards


@payment_router.post('/add-card')
async def add_card(
        holder_name: str,
        number: str,
        expiry_month: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        return HTTPException(status_code=403, detail='Forbidden')

    user_id = token.get('user_id')
    query = select(saved_cards).where(saved_cards.c.card_number == number)
    data = await session.execute(query)
    dataa = data.scalar()
    if dataa:
        return {'success': False, 'message': 'This card already exists'}
    query1 = insert(saved_cards).values(
        user_id=user_id,
        card_holder_name=holder_name,
        card_number=number,
        expiry_month=expiry_month
    )
    await session.execute(query1)
    await session.commit()
    return {'success': True}


@payment_router.patch('/edit-card')
async def update_card(
        card_id: int,
        holder_name: str,
        number: str,
        expiry_month: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session),
):
    if token is None:
        raise HTTPException(status_code=403, detail='Forbidden')

    user_id = token.get('user_id')

    query = select(saved_cards).where((saved_cards.c.user_id == user_id) & (saved_cards.c.id == card_id))
    data = await session.execute(query)
    card_data = data.fetchall()
    if not card_data:
        raise HTTPException(status_code=404, detail="Card not found")

    query1 = (
        update(saved_cards)
        .where((saved_cards.c.user_id == user_id) & (saved_cards.c.id == card_id))
        .values(
            card_holder_name=holder_name,
            card_number=number,
            expiry_month=expiry_month,
        )
    )
    await session.execute(query1)
    await session.commit()

    return {'success': True, 'detail': 'Card Edited!'}


@payment_router.delete('/delete-card')
async def delete_card(
        card_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        return HTTPException(status_code=403, detail='Forbidden')
    user_id = token.get('user_id')
    query = select(saved_cards).where((saved_cards.c.user_id == user_id) & (saved_cards.c.id == card_id))
    data = await session.execute(query)
    card_data = data.first()
    if card_data is None:
        return HTTPException(status_code=404)

    query1 = delete(saved_cards).where((saved_cards.c.user_id == user_id) & (saved_cards.c.id == card_id))
    await session.execute(query1)
    await session.commit()
    return HTTPException(status_code=204)


################ Payment #################################


@payment_router.get('/get-payment', response_model=dict)
async def get_payment(
        trainer_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        raise HTTPException(status_code=403, detail='Forbidden')

    user_id = token.get('user_id')

    user_cards = await session.execute(select(saved_cards).where(saved_cards.c.user_id == user_id))
    user_cards_data = user_cards.all()

    trainer_info = await session.execute(select(trainer.c.cost, trainer.c.description)
                                         .where(trainer.c.id == trainer_id))
    trainer_data = trainer_info.all()

    if not user_cards_data:
        raise HTTPException(status_code=404, detail='User data not found')
    if not trainer_data:
        raise HTTPException(status_code=404, detail='Trainer data not found')

    users_trainer_info = await session.execute(
        select(users).select_from(join(trainer, users, trainer.c.user_id == users.c.id)).where(
            trainer.c.id == trainer_id)
    )
    users_trainer_data = users_trainer_info.all()

    if not users_trainer_data:
        raise HTTPException(status_code=404, detail='Trainer full name not found')

    user_names = [user.name for user in users_trainer_data]

    data_json = r.get('datetime')
    if data_json is None:
        return {"message": "No data found in Redis"}
    data = json.loads(data_json.decode("utf-8"))

    payment_info = {
        "user_cards": [{"card_id": card.id, "card_number": card.card_number} for card in user_cards_data],
        "trainer_info": {"full_name": user_names[0], 'description': trainer_data[0].description,
                         "cost": trainer_data[0].cost},
        "booked_data": data
    }

    return payment_info


@payment_router.post('/make_payment')
async def payment(
        trainer_id: int,
        card_id: int,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        return HTTPException(status_code=403, detail='Forbidden')
    user_id = token.get('user_id')

    get_amount = select(trainer.c.cost).where(trainer.c.id == trainer_id)
    amount_data = await session.execute(get_amount)
    amount = amount_data.scalar()

    if amount is None:
        return HTTPException(status_code=404, detail='Trainer not found')

    check_card = (
        update(saved_cards)
        .where((saved_cards.c.id == card_id) & (saved_cards.c.balance >= amount))
        .values(balance=saved_cards.c.balance - amount)
    )
    await session.execute(check_card)

    select_card = select(saved_cards).where(saved_cards.c.id == card_id)
    updated_card = await session.execute(select_card)
    updated_card_data = updated_card.fetchone()

    if updated_card_data is not None:
        new_payment = insert(user_payment).values(
            user_id=user_id,
            trainer_id=trainer_id,
            amount=amount,
            card_id=card_id
        )
        data_json = r.get('datetime')
        if data_json is None:
            return {"message": "No data found in Redis"}
        data = json.loads(data_json.decode("utf-8"))
        print(data)
        query1 = insert(booked_trainer).values(
            user_id=user_id,
            trainer_id=trainer_id,
            date=data.get('date')
        )
        query = update(trainer).where(trainer.c.id == trainer_id).values(
            active_clients=trainer.c.active_clients + 1
        )
        await session.execute(query1)
        await session.execute(new_payment)
        await session.execute(query)
        await session.commit()
        return {'success': True, 'detail': 'Payment successfully'}
    else:
        return HTTPException(status_code=400, detail='Insufficient balance')

