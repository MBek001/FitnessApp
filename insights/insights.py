from datetime import datetime
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from auth.auth import is_admin, check_date
from auth.utils import verify_token
from database import get_async_session
from sqlalchemy import select, insert
from fastapi import APIRouter

from .schemes import InsightsPost, GetInsights
from models.models import insights

insights_router = APIRouter()


@insights_router.post('/add_insights')
async def add(blog: InsightsPost, token: dict = Depends(verify_token),
              session: AsyncSession = Depends(get_async_session)):
    try:
        user_id = token['user_id']
        if token and await is_admin(token, session):
            query = insert(insights).values(user_id=int(user_id), calories=dict(blog)['calories'],
                                            steps=dict(blog)['steps'], time_spent=dict(blog)['time_spent'],
                                            heartbeat=dict(blog)['heartbeat'], date=dict(blog)['date'],
                                            day=dict(blog)['day'])
            await session.execute(query)
            await session.commit()
            return {'success': True, 'message': 'Insights added!', 'data': blog}
    except Exception as e:
        return {"success": False, "message": f"{e}"}


@insights_router.get('/insights', response_model=dict)
async def getting(blog_data: str, token: dict = Depends(verify_token),
                  session: AsyncSession = Depends(get_async_session)):
    try:
        if token and await is_admin(token, session):
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
