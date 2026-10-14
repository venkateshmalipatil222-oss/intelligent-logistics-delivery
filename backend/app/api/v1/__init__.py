"""
API v1 router package.
"""
from fastapi import APIRouter
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.users import router as users_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["System & Health"])
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication & Security"])
api_router.include_router(users_router, prefix="/users", tags=["User Management & RBAC"])
