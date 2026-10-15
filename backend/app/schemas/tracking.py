from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class DriverGPSPing(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    speed_kmph: Optional[float] = Field(0.0, ge=0.0)
    accuracy_meters: Optional[float] = Field(None, ge=0.0)
    heading_degrees: Optional[float] = Field(None, ge=0.0, le=360.0)
    timestamp: Optional[datetime] = None


class LiveCoordinate(BaseModel):
    name: str
    latitude: float
    longitude: float


class LiveTrackingState(BaseModel):
    delivery_id: int
    delivery_number: str
    order_id: int
    order_number: str
    status: str
    driver_id: int
    driver_name: str
    driver_phone: Optional[str] = None
    driver_rating: float
    vehicle_registration: Optional[str] = None
    vehicle_type: Optional[str] = None
    origin_warehouse: LiveCoordinate
    destination: LiveCoordinate
    current_driver_location: LiveCoordinate
    remaining_distance_km: float
    estimated_arrival_time: Optional[datetime] = None
    uncertainty_buffer_minutes: float
    confidence_lower_bound: Optional[datetime] = None
    confidence_upper_bound: Optional[datetime] = None
    traffic_condition: str
    delay_risk_level: str
    delay_explanation: str
    is_delayed: bool
    last_ping_seconds_ago: Optional[float] = None
    is_telemetry_stale: bool
    otp_required: bool
    connection_mode: str = "REST_SNAPSHOT"

    model_config = ConfigDict(from_attributes=True)
