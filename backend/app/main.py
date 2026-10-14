import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.app.core.config import settings
from backend.app.core.database import check_db_connection
from backend.app.core.logger import logger
from backend.app.api.v1 import api_router
from backend.app.api.v1.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager: executed on startup and graceful shutdown.
    """
    logger.info(f"Starting {settings.PROJECT_NAME} in [{settings.ENVIRONMENT}] mode...")
    
    # Verify database connectivity on startup
    db_status = check_db_connection()
    if db_status.get("status") == "connected":
        logger.info(f"Database connection verified: {db_status['dialect']} ({db_status['database']}) in {db_status['latency_ms']}ms")
    else:
        logger.warning(f"Database connection failed or degraded on startup: {db_status}")

    yield

    logger.info(f"Shutting down {settings.PROJECT_NAME}...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Production-grade full-stack backend for the Intelligent Logistics & Delivery "
        "Optimization Platform (ILDO). Features multi-factor driver assignments, "
        "Dijkstra & multi-stop route optimization, real-time WebSocket GPS tracking, "
        "dynamic ETA calculations, automated delay risk detection, and proof-of-delivery validation."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Middleware measuring request latency and injecting custom telemetry headers.
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{round(process_time * 1000, 2)}ms"
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global catch-all exception handler preventing internal traceback leaks to clients.
    """
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected server error occurred. Please contact system administration.",
            "path": request.url.path,
        },
    )


# Mount versioned API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Top-level direct health check for infrastructure monitors
app.include_router(health_router, prefix="/health", tags=["System & Health"])


@app.get("/", tags=["Root"])
def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs",
        "api_v1": settings.API_V1_STR,
    }
