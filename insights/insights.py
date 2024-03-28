from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from starlette import status

from auth.utils import verify_token
from database import get_async_session
from sqlalchemy import select, insert, delete
from fastapi import APIRouter

from .schemes import InsightsPost, GetInsights
from models.models import insights, users

insights_router = APIRouter()


@insights_router.post('/add_insights')
async def add(blog: InsightsPost, token: dict = Depends(verify_token),
              session: AsyncSession = Depends(get_async_session)):
    user_id = token.get('user_id')

    try:
        user_id = token['user_id']
        query = insert(insights).values(user_id=int(user_id), calories=dict(blog)['calories'],
                                        steps=dict(blog)['steps'], time_spent=dict(blog)['time_spent'],
                                        heartbeat=dict(blog)['heartbeat'], date=dict(blog)['date'],
                                        day=dict(blog)['day'])
        await session.execute(query)
        await session.commit()
        return {'success': True, 'message': 'Insights added!', 'data': blog}
    except Exception as e:
        return {"success": False, "message": f"{e}"}


@insights_router.get('/insights_in_date', response_model=dict)
async def getting(blog_data: str, token: dict = Depends(verify_token),
                  session: AsyncSession = Depends(get_async_session)):
    try:
        if token:
            datetime_object = datetime.strptime(blog_data, "%Y-%m-%d")
            query = select(insights).where(insights.c.date == datetime_object)
            blog_date = await session.execute(query)
            await session.execute(query)
            query = blog_date.fetchone()
            day = (query[-2]).value[0]
            date = query[-1].strftime("%Y-%m-%d")
            data = {
                "id": query[0],
                "calories": query[2],
                "steps": query[3],
                "time_spent": query[4],
                "heartbeat": query[5],
                "day": day,
                "date": date,
            }
            return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "message": "No insights the day!"}


@insights_router.get("/insights_info", response_model=list[GetInsights])
async def gett(token: dict = Depends(verify_token),
               session: AsyncSession = Depends(get_async_session)):
    try:
        if token:
            query = select(insights)
            query = await session.execute(query)
            return query
        else:
            return {"success": False, "message": "No login"}
    except Exception as e:
        return {"success": False, "message": f"{e}"}


@insights_router.delete('/delete_insight')
async def delete_insights(insights_id:int, token: dict = Depends(verify_token),
               session: AsyncSession = Depends(get_async_session)):
    try:
        user_id = token.get('user_id')
        result = await session.execute(
            select(users).where(
                (users.c.id == user_id) &
                (users.c.is_admin == True)
            )
        )
        if token and result.scalar() == 1:
            query = delete(insights).where(insights.c.id == insights_id)
            await session.execute(query)
            await session.commit()
            await session.close()
            return {"success": True, "message": "Insights deleted!"}
        else:
            return {"success": True, "message": "User is not admin!"}

    except Exception as e:
        return {"success": False, "message": f"{e}"}