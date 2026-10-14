"""
API v1 router package.
"""
from fastapi import APIRouter
from backend.app.api.v1.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["System & Health"])
