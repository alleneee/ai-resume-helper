from fastapi import APIRouter
from app.api import resume, analysis

api_router = APIRouter()
api_router.include_router(resume.router)
api_router.include_router(analysis.router) 