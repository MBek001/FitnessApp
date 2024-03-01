import json
import os
import secrets
import redis
from typing import List

import aiofiles

from category.category import category_router
from insights.insights import insights_router
from fastapi import Body, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, update, func, join, delete
from starlette.responses import FileResponse, RedirectResponse

from auth.utils import verify_token
from models.models import *
from fastapi import FastAPI, APIRouter, HTTPException, Depends
from auth.auth import register_router
from database import get_async_session
from starlette import status

from models.models import trainer
from scheme import TrainerDetailResponse
from trainer.trainer import trainer_router

r = redis.Redis(host='localhost', port=6379, db=0)
app = FastAPI(title='Fitnessapp', version='1.0.0')
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
        data = {
            'date': date,
            'hours': hour,
            'minutes': minute
        }
        r.set('datetime', json.dumps(data))

        return {'success': True}
    else:
        return {'success': False, 'detail': " Trainer is not available at the selected time."}


@router.post('/add-card')
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


@router.patch('/edit-card')
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


@router.get('/get-cards')
async def get_cards(
        number: int,
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


@router.delete('/delete-card')
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


@router.get('/get-payment', response_model=dict)
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
    print(user_cards_data)
    trainer_info = await session.execute(select(trainer.c.full_name, trainer.c.cost, trainer.c.description).where(trainer.c.id == trainer_id))
    trainer_data = trainer_info.all()

    if not user_cards_data:
        raise HTTPException(status_code=404, detail='user Data not found')
    if not trainer_data:
        raise HTTPException(status_code=404, detail='trainer Data not found')

    data_json = r.get('datetime')
    if data_json is None:
        return {"message": "No data found in Redis"}
    data = json.loads(data_json.decode("utf-8"))

    payment_info = {
        "user_cards": [{"card_id": card.id, "card_number": card.card_number} for card in user_cards_data],
        "trainer_info": [{"full_name": trainerinfo.full_name, 'description': trainerinfo.description, "cost": trainerinfo.cost} for trainerinfo in trainer_data],
        "booked_data": data
    }
    print(payment_info)
    return payment_info


@router.post('/payment')
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
        query = update(trainer).where(trainer.c.id == trainer_id).values(
            active_clients=trainer.c.active_clients + 1
        )
        await session.execute(new_payment)
        await session.execute(query)
        await session.commit()
        return {'success': True, 'detail': 'Payment successfully'}
    else:
        return HTTPException(status_code=400, detail='Insufficient balance')


@router.post('/upload-file')
async def upload_file(
        uploadfile: UploadFile,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    user_id = token.get('user_id')
    result = await session.execute(
        select(users).where(
            (users.c.id == user_id)&
            (users.c.is_admin == True)
        )
    )
    if not result.scalar():
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)

    try:
        out_file = f'files/{uploadfile.filename}'
        async with aiofiles.open(out_file, "wb") as f:
            content = await uploadfile.read()
            await f.write(content)
        hashcode = secrets.token_hex(32)
        query = insert(exercises).values(video_url=out_file, video_hash=hashcode)
        await session.execute(query)
        await session.commit()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {'success': True, 'message': 'Uploaded successfully'}


@router.get('/get-file/{hashcode}')
async def download_file(
        hashcode: str
):
    if hashcode is None:
        raise HTTPException(status_code=400, detail='Invalid hashcode')

    file_url = f'http://127.0.0.1:8000/main/download-file/{hashcode}'
    return {'file-link': file_url}


@router.get('/download-file/{hashcode}', response_class=RedirectResponse)
async def download_file(
        hashcode: str,
        session: AsyncSession = Depends(get_async_session)
):
    if hashcode is None:
        raise HTTPException(status_code=400, detail='Invalid hashcode')

    query = select(exercises).where(exercises.c.video_hash == hashcode)
    video__data = await session.execute(query)
    video_data = video__data.one()
    return FileResponse(video_data.video_url)


@router.post("/add-notification-news")
async def add_notification(title: str,news_data: str,useer_id: int , token: dict = Depends(verify_token), session: AsyncSession = Depends(get_async_session)):
    user_id = token.get('user_id')
    result = await session.execute(
        select(users).where(
            (users.c.id == user_id) &
            (users.c.is_admin == True)
        )
    )

    if not result.scalar():
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
    query = insert(news).values(
        user_id=useer_id,
        title=title,
        news=news_data
    )
    await session.execute(query)
    await session.commit()
    return {"message": "Notification sent successfully"}


@router.post("/add-notification-events")
async def add_notification(news_data: str, title: str, token: dict = Depends(verify_token), session: AsyncSession = Depends(get_async_session)):
    user_id = token.get('user_id')
    result = await session.execute(
        select(users).where(
            (users.c.id == user_id) &
            (users.c.is_admin == True)
        )
    )
    if not result.scalar():
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
    query = insert(events).values(
        title=title,
        event=news_data
    )
    await session.execute(query)
    await session.commit()
    return {"message": "Notification sent successfully"}


@router.get("/notification-news")
async def send_notification_news(
        token: dict = Depends(verify_token),
        session : AsyncSession = Depends(get_async_session)
):
    user_id = token.get('user_id')

    three_days_ago = datetime.utcnow() - timedelta(days=3)
    query = select(news).where(news.c.created_at >= three_days_ago,news.c.user_id==user_id)
    result = await session.execute(query)

    notif = result.all()
    res =[]
    for i in notif:
        notific=i.news
        vohti=""
        vohti+=str(i.created_at.hour)
        vohti+=':'
        vohti+=str(i.created_at.minute)
        message=i.title
        dictjon={
            "message": message,
            "news": notific,
            "time": vohti

        }
        res.append(dictjon)
        print(i)
    return res


@router.get("/notification-events")
async def send_notification_events(
        session : AsyncSession=Depends(get_async_session)
):
    three_days_ago = datetime.utcnow() - timedelta(days=3)
    query = select(events).where(events.c.created_at >= three_days_ago)
    result = await session.execute(query)
    notif = result.all()
    res =[]
    for i in notif:
        notific = i.event
        vohti = ""

        vohti += str(i.created_at.hour)
        vohti += ':'
        vohti += str(i.created_at.minute)
        message = i.title
        dictjon = {
            "title": message,
            "events": notific,
            "time": vohti,

        }
        res.append(dictjon)
        print(i)
    return res


@router.get("/notification-all")
async def send_notification_all(
        token: dict=Depends(verify_token),
        session : AsyncSession=Depends(get_async_session)
):
    user_id = token.get('user_id')

    three_days_ago = datetime.utcnow() - timedelta(days=3)
    query = select(news).where(news.c.created_at >= three_days_ago,news.c.user_id==user_id)
    result = await session.execute(query)
    notif=result.all()
    query1=select(events)
    result1= await session.execute(query1)
    notif1=result1.all()
    res=[]
    for i in notif:
        notific=i.news
        vohti=""
        vohti+=str(i.created_at.hour)
        vohti+=':'
        vohti+=str(i.created_at.minute)
        message=i.title
        dictjon={
            "message": message,
            "news": notific,
            "time": vohti

        }
        res.append(dictjon)
    for i in notif1:
        notific = i.event
        vohti = ""

        vohti += str(i.created_at.hour)
        vohti += ':'
        vohti += str(i.created_at.minute)
        message = i.title
        dictjon = {
            "title": message,
            "events": notific,
            "time": vohti,

        }
        res.append(dictjon)
    return res


@router.get('/get-languages')
async def get_languages():
    res = []
    for i in LanguageEnum:
        res.append(i)

    return res


@router.patch('/edit-user-language')
async def edit_user(
        new_language: str,
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    if token is None:
        return HTTPException(status_code=403, detail='Forbidden')
    user_id = token.get('user_id')

    query = update(users).where(users.c.id == user_id).values(language=new_language)
    await session.execute(query)
    await session.commit()
    return {'success': True, 'detail': f'Languages Successfully Updated {new_language}'}


@router.post("/add_trainers")
async def add_trainer(
        user_id:int,
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
            (trainer.c.user_id == user_idd)
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


@router.delete("/delete_trainers")
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


@router.get("/trainer-detail")
async def get_trainer_detail(
    trainer_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    result = select(trainer).join(users, trainer.c.user_id == users.c.id).filter(trainer.c.user_id == trainer_id).with_only_columns(
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
    print(trainer_data)
    if trainer_data is None:
        raise HTTPException(status_code=404, detail="Trainer not found")

    return TrainerDetailResponse(
        user_id=trainer_data.user_id,
        name=trainer_data.name,
        experience=trainer_data.experience,
        active_clients=trainer_data.active_clients,
        phone_number=trainer_data.phone_number,
        description=trainer_data.description
    )



app.include_router(register_router, prefix='/auth')
app.include_router(register_router, prefix='/user')
app.include_router(insights_router, prefix='/insights')
app.include_router(trainer_router, prefix='/trainer')
app.include_router(category_router, prefix='/category')
app.include_router(router, prefix='/main')
