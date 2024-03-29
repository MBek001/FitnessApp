import secrets
import redis
import aiofiles
from fastapi import Body, UploadFile
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

from models.models import category
from scheme import *
from sqlalchemy.exc import SQLAlchemyError

from trainer.trainer import trainer_router
from category.category import category_router
from insights.insights import insights_router
from payment.payment import payment_router

r = redis.Redis(host='redis', port=6379, db=0)
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

    user_level_query = select(user_level.c.level_id).where(user_level.c.user_id == user_id)
    user_level_result = await session.execute(user_level_query)
    user_level_id = user_level_result.scalar()

    category_query = select(category.c.name).where(category.c.level_id == user_level_id)
    workout_categories_result = await session.execute(category_query)
    workout_categories = workout_categories_result.all()

    categories = [category.name for category in workout_categories]

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


    return {
        "User": user_dict,
        "Workout Plan": plan_dict,
        "New Workouts": new_workouts_formatted,
        "Categories": categories
    }


@router.post('/user_workout')
async def login(level_id: UserWorkout, session: AsyncSession = Depends(get_async_session),
                token: dict = Depends(verify_token)):
    try:
        user_id = token['user_id']
        if token:
            query = insert(user_level).values(user_id=int(user_id), level_id=int(dict(level_id)['level_id']))
            await session.execute(query)
            await session.commit()
            return {"success": True, "message": "Workout added!"}
    except Exception as e:
        return {"success": False, "message": f"{e}"}


@router.get('/user_workout_info')
async def getting(token: dict = Depends(verify_token), session: AsyncSession = Depends(get_async_session)):
    if not token:
        raise HTTPException(status_code=401, detail='Unauthorized')

    try:
        user_id = token.get('user_id')
        query = await session.execute(select(user_level.c.level_id).where(user_level.c.user_id == user_id))
        level_id = query.scalars().fetchall()[0]
        query1 = await session.execute(select(level.c.name).where(level.c.id == level_id))
        res = query1.scalars().fetchall()
        return res
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f'{e}')


@router.post("/comment_review/")
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
async def delete_comment(comment_id: int, token: dict = Depends(verify_token),
                         session: AsyncSession = Depends(get_async_session)):
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


@router.get('/reviews-info/')
async def get_comment(trainer_id: int,
                      session: AsyncSession = Depends(get_async_session)):
    try:

        query = select(review.c.rating, review.c.comment, review.c.trainer_id, trainer.c.id, trainer.c.user_id,  users.c.name , users.c.id) \
            .where(review.c.trainer_id == trainer_id, trainer.c.id == trainer_id, trainer.c.user_id == users.c.id)

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
                'id': item.id,
                'user': item.name,
                'rating': item.rating,
                'comment': item.comment
            }
            res.append(comment_dict)

        return res

    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post('/upload-video')
async def upload_file(
        uploadfile: UploadFile,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    user_id = token.get('user_id')
    result = await session.execute(
        select(users).where(
            (users.c.id == user_id) &
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


@router.post("/add-notification-news")
async def add_notification(title: str, news_data: str, useer_id: int, token: dict = Depends(verify_token),
                           session: AsyncSession = Depends(get_async_session)):
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
async def add_notification(news_data: str, title: str, token: dict = Depends(verify_token),
                           session: AsyncSession = Depends(get_async_session)):
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
        session: AsyncSession = Depends(get_async_session)
):
    user_id = token.get('user_id')

    three_days_ago = datetime.utcnow() - timedelta(days=3)
    query = select(news).where(news.c.created_at >= three_days_ago, news.c.user_id == user_id)
    result = await session.execute(query)

    notif = result.all()
    res = []
    for i in notif:
        notific = i.news
        vohti = ""
        vohti += str(i.created_at.hour)
        vohti += ':'
        vohti += str(i.created_at.minute)
        message = i.title
        dictjon = {
            "message": message,
            "news": notific,
            "time": vohti

        }
        res.append(dictjon)

    return res


@router.get("/notification-events")
async def send_notification_events(
        session: AsyncSession = Depends(get_async_session)
):
    three_days_ago = datetime.utcnow() - timedelta(days=3)
    query = select(events).where(events.c.created_at >= three_days_ago)
    result = await session.execute(query)
    notif = result.all()
    res = []
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
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)
):
    user_id = token.get('user_id')

    three_days_ago = datetime.utcnow() - timedelta(days=3)
    query = select(news).where(news.c.created_at >= three_days_ago, news.c.user_id == user_id)
    result = await session.execute(query)
    notif = result.all()
    query1 = select(events)
    result1 = await session.execute(query1)
    notif1 = result1.all()
    res = []
    for i in notif:
        notific = i.news
        vohti = ""
        vohti += str(i.created_at.hour)
        vohti += ':'
        vohti += str(i.created_at.minute)
        message = i.title
        dictjon = {
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


@router.get('/get-video/{exercises_id}')
async def download_file(
        exercises_id: int
):
    if exercises_id is None:
        raise HTTPException(status_code=400, detail='Invalid hashcode')

    file_url = f'http://159.65.49.146:8000//main/download-video/{exercises_id}'
    return {'file-link': file_url}


@router.get('/download-video/{exercises_id}', response_class=RedirectResponse)
async def download_file(
        exercises_id: int,
        session: AsyncSession = Depends(get_async_session)
):
    try:
        if exercises_id is None:
            raise HTTPException(status_code=400, detail='Invalid hashcode')
        query = select(exercises).where(exercises.c.id == exercises_id)
        video__data = await session.execute(query)
        video_data = video__data.one()
        return FileResponse(video_data.video_url)
    except Exception as e:
        return {"success": False, "message": f"{e}"}


@router.get('/get-photo')
async def download_file(
        category_id: int
):
    if category_id is None:
        raise HTTPException(status_code=400, detail='Invalid hashcode')

    file_url = f'http://159.65.49.146:8000//main/download-photo/{category_id}'
    return {'file-link': file_url}


@router.get('/download-photo/{category_id}', response_class=RedirectResponse)
async def download_file(
        category_id: int,
        session: AsyncSession = Depends(get_async_session)
):
    try:
        if category_id is None:
            raise HTTPException(status_code=400, detail='Invalid hashcode')

        query = select(category).where(category.c.id == category_id)
        video__data = await session.execute(query)
        video_data = video__data.one()
        return FileResponse(video_data.photo_url)
    except Exception as e:
        return {"success": False, "message": f"{e}"}


app.include_router(register_router, prefix='/auth')
app.include_router(router, prefix='/main')
app.include_router(insights_router, prefix='/insights')
app.include_router(category_router, prefix='/category')
app.include_router(trainer_router, prefix='/trainer')
app.include_router(payment_router, prefix='/payment')


