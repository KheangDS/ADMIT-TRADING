from fastapi import APIRouter
from app.api.v1.endpoints import upload, analytics, chat, admin

api_router = APIRouter()
api_router.include_router(upload.router, tags=["upload"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

