import os
from datetime import datetime, date
from typing import List, Union

import aiofiles
import secrets
from fastapi import FastAPI, Depends, HTTPException, APIRouter, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, update, func

from auth.auth import register_router


app = FastAPI(title='FitnessApp', version='1.0.0')
router = APIRouter()

app.include_router(register_router, prefix='/auth')
app.include_router(router, prefix='/main')
