from fastapi import FastAPI, APIRouter
from auth.auth import register_router

app = FastAPI(title='Netflix', version='1.0.0')

router = APIRouter()

app.include_router(register_router, prefix='/auth')
app.include_router(router, prefix='/main')
