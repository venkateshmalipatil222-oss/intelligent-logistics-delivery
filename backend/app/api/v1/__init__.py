"""
API v1 router package.
"""
from fastapi import APIRouter
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.users import router as users_router
from backend.app.api.v1.warehouses import router as warehouses_router
from backend.app.api.v1.vehicles import router as vehicles_router
from backend.app.api.v1.drivers import router as drivers_router
from backend.app.api.v1.orders import router as orders_router
from backend.app.api.v1.deliveries import router as deliveries_router
from backend.app.api.v1.intelligence import router as intelligence_router
from backend.app.api.v1.tracking import router as tracking_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["System & Health"])
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication & Security"])
api_router.include_router(users_router, prefix="/users", tags=["User Management & RBAC"])
api_router.include_router(warehouses_router, prefix="/warehouses", tags=["Warehouse Hub"])
api_router.include_router(vehicles_router, prefix="/vehicles", tags=["Fleet & Vehicles"])
api_router.include_router(drivers_router, prefix="/drivers", tags=["Driver Operations"])
api_router.include_router(orders_router, prefix="/orders", tags=["Order Pipeline"])
api_router.include_router(deliveries_router, prefix="/deliveries", tags=["Delivery Dispatch & State Machine"])
api_router.include_router(intelligence_router, prefix="/intelligence", tags=["Optimization & Algorithmic Intelligence"])
api_router.include_router(tracking_router, prefix="/tracking", tags=["Real-Time Geolocation & Live Operations"])
