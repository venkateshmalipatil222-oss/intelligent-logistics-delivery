import time
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.app.core.config import settings
from backend.app.core.logger import logger

db_url = settings.get_database_url()

# Configure engine arguments based on database dialect
connect_args = {}
engine_kwargs = {
    "pool_pre_ping": True,
}

if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    engine_kwargs["connect_args"] = connect_args
else:
    # MySQL specific connection pooling
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_recycle"] = 3600

engine = create_engine(db_url, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a transactional database session per request.
    Automatically closes the session when the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"Database session rollback due to exception: {e}")
        raise
    finally:
        db.close()


def check_db_connection() -> dict:
    """
    Executes a lightweight query to verify connectivity and measure latency.
    """
    start_time = time.time()
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar()
            latency_ms = round((time.time() - start_time) * 1000, 2)
            if result == 1:
                return {
                    "status": "connected",
                    "dialect": engine.dialect.name,
                    "database": settings.MYSQL_DB if not db_url.startswith("sqlite") else settings.SQLITE_DB_PATH,
                    "latency_ms": latency_ms,
                }
            return {
                "status": "degraded",
                "message": "Unexpected response from database",
                "latency_ms": latency_ms,
            }
    except Exception as exc:
        latency_ms = round((time.time() - start_time) * 1000, 2)
        logger.error(f"Database connectivity check failed: {exc}")
        return {
            "status": "disconnected",
            "error": str(exc),
            "latency_ms": latency_ms,
        }
