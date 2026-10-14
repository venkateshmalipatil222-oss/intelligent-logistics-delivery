import os
import urllib.parse
from pathlib import Path
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Determine base paths: check backend directory or workspace root for .env
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_ENV = BASE_DIR.parent / ".env"
LOCAL_ENV = BASE_DIR / ".env"
ENV_FILE = str(LOCAL_ENV) if LOCAL_ENV.exists() else str(ROOT_ENV)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "Intelligent Logistics & Delivery Optimization Platform (ILDO)"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = Field(default="ildo-dev-secret-key-minimum-32-characters-long-2026", min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # MySQL Configuration
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_DB: str = "ildo_db"

    # Explicit Database URL override if provided
    DATABASE_URL: Union[str, None] = None

    # Fallback to SQLite (useful for automated testing or non-MySQL machines)
    USE_SQLITE_FALLBACK: bool = False
    SQLITE_DB_PATH: str = "ildo_dev.db"

    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # WebSocket Settings
    WS_HEARTBEAT_INTERVAL_SECONDS: int = 30

    # Algorithmic & Engine Defaults
    MAX_DELIVERY_RADIUS_KM: float = 50.0
    DEFAULT_AVERAGE_SPEED_KMH: float = 35.0
    DEFAULT_STOP_SERVICE_MINUTES: int = 10
    DEFAULT_ETA_UNCERTAINTY_BUFFER_MINUTES: int = 5
    DELAY_RISK_THRESHOLD_MINUTES: int = 15

    # Cost Parameters
    FUEL_PRICE_PER_LITER: float = 1.50
    DEFAULT_VEHICLE_EFFICIENCY_KMPL: float = 12.0
    DRIVER_HOURLY_RATE: float = 18.00
    VEHICLE_MAINTENANCE_PER_KM: float = 0.15
    BASE_DISPATCH_FEE: float = 5.00

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    def get_database_url(self) -> str:
        """
        Returns a clean database URL. Encodes the password safely if constructing from components.
        """
        if self.DATABASE_URL and self.DATABASE_URL.strip():
            return self.DATABASE_URL.strip()

        if self.USE_SQLITE_FALLBACK:
            return f"sqlite:///{self.SQLITE_DB_PATH}"

        encoded_password = urllib.parse.quote_plus(self.MYSQL_PASSWORD)
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{encoded_password}@"
            f"{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset=utf8mb4"
        )


settings = Settings()
