from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from backend.app.models.enums import (
    VehicleType,
    VehicleStatus,
    DriverStatus,
    OrderStatus,
    DeliveryPriority,
    DelayRiskCategory,
)


# -----------------------------------------------------------------------------
# Warehouse Schemas
# -----------------------------------------------------------------------------
class WarehouseBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    code: str = Field(..., min_length=2, max_length=50)
    address_line1: str = Field(..., min_length=3, max_length=255)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    postal_code: str = Field(..., min_length=3, max_length=20)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    capacity_sqft: float = Field(default=10000.0, gt=0)
    contact_phone: Optional[str] = Field(None, max_length=50)
    is_active: bool = True


class WarehouseCreate(WarehouseBase):
    manager_id: Optional[int] = None


class WarehouseUpdate(BaseModel):
    name: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    capacity_sqft: Optional[float] = Field(None, gt=0)
    contact_phone: Optional[str] = None
    manager_id: Optional[int] = None
    is_active: Optional[bool] = None


class WarehouseResponse(WarehouseBase):
    id: int
    manager_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# Vehicle Schemas
# -----------------------------------------------------------------------------
class VehicleBase(BaseModel):
    registration_number: str = Field(..., min_length=3, max_length=50)
    model: str = Field(..., min_length=2, max_length=100)
    vehicle_type: VehicleType = VehicleType.VAN
    max_weight_capacity_kg: float = Field(..., gt=0)
    max_volume_capacity_m3: float = Field(..., gt=0)
    fuel_type: str = Field(default="DIESEL", max_length=50)
    fuel_efficiency_kmpl: float = Field(default=12.0, gt=0)
    status: VehicleStatus = VehicleStatus.AVAILABLE
    current_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    current_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    model: Optional[str] = None
    vehicle_type: Optional[VehicleType] = None
    max_weight_capacity_kg: Optional[float] = Field(None, gt=0)
    max_volume_capacity_m3: Optional[float] = Field(None, gt=0)
    fuel_type: Optional[str] = None
    fuel_efficiency_kmpl: Optional[float] = Field(None, gt=0)
    status: Optional[VehicleStatus] = None
    current_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    current_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)


class VehicleResponse(VehicleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# Driver Schemas
# -----------------------------------------------------------------------------
class DriverBase(BaseModel):
    license_number: str = Field(..., min_length=5, max_length=100)
    current_vehicle_id: Optional[int] = None
    status: DriverStatus = DriverStatus.AVAILABLE


class DriverCreate(DriverBase):
    user_id: int


class DriverUpdate(BaseModel):
    license_number: Optional[str] = None
    current_vehicle_id: Optional[int] = None
    status: Optional[DriverStatus] = None


class DriverLocationUpdate(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)


class DriverResponse(DriverBase):
    id: int
    user_id: int
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    last_location_updated_at: Optional[datetime] = None
    total_deliveries_completed: int
    total_deliveries_failed: int
    rating: float
    active_deliveries_count: int
    created_at: datetime
    updated_at: datetime

    # Embedded user information if available
    driver_name: Optional[str] = None
    driver_email: Optional[str] = None
    driver_phone: Optional[str] = None
    vehicle_registration: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# Package Schemas
# -----------------------------------------------------------------------------
class PackageBase(BaseModel):
    weight_kg: float = Field(..., gt=0, description="Weight in kilograms")
    length_cm: float = Field(default=20.0, gt=0)
    width_cm: float = Field(default=15.0, gt=0)
    height_cm: float = Field(default=10.0, gt=0)
    category: str = Field(default="GENERAL", max_length=100)
    is_fragile: bool = False
    requires_cold_storage: bool = False


class PackageCreate(PackageBase):
    tracking_number: Optional[str] = None


class PackageUpdate(BaseModel):
    weight_kg: Optional[float] = Field(None, gt=0)
    length_cm: Optional[float] = Field(None, gt=0)
    width_cm: Optional[float] = Field(None, gt=0)
    height_cm: Optional[float] = Field(None, gt=0)
    category: Optional[str] = None
    is_fragile: Optional[bool] = None
    requires_cold_storage: Optional[bool] = None
    is_ready_for_dispatch: Optional[bool] = None


class PackageResponse(PackageBase):
    id: int
    order_id: int
    tracking_number: str
    volume_m3: float
    is_ready_for_dispatch: bool
    prepared_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# Order Schemas
# -----------------------------------------------------------------------------
class OrderBase(BaseModel):
    warehouse_id: Optional[int] = None
    destination_address: str = Field(..., min_length=3, max_length=255)
    destination_city: str = Field(..., min_length=2, max_length=100)
    destination_state: str = Field(..., min_length=2, max_length=100)
    destination_postal_code: str = Field(..., min_length=3, max_length=20)
    destination_latitude: float = Field(..., ge=-90.0, le=90.0)
    destination_longitude: float = Field(..., ge=-180.0, le=180.0)
    priority: DeliveryPriority = DeliveryPriority.MEDIUM


class OrderCreate(OrderBase):
    customer_id: Optional[int] = None  # Inferred for CUSTOMER role, required for ADMIN/MANAGER
    promised_delivery_time: Optional[datetime] = None
    package: PackageBase


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    reason: Optional[str] = None


class OrderResponse(OrderBase):
    id: int
    order_number: str
    customer_id: int
    status: OrderStatus
    estimated_distance_km: float
    estimated_delivery_cost: float
    promised_delivery_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    package: Optional[PackageResponse] = None

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# Delivery Schemas
# -----------------------------------------------------------------------------
class DeliveryDispatchCreate(BaseModel):
    order_id: int
    driver_id: int
    vehicle_id: int
    warehouse_id: int


class DeliveryStatusTransition(BaseModel):
    to_status: OrderStatus
    reason: Optional[str] = None
    notes: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)


class DeliveryVerifyOTP(BaseModel):
    otp_code: str = Field(..., min_length=4, max_length=10)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    notes: Optional[str] = None


class DeliveryStatusHistoryResponse(BaseModel):
    id: int
    delivery_id: int
    from_status: Optional[OrderStatus] = None
    to_status: OrderStatus
    changed_by_user_id: Optional[int] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class DeliveryResponse(BaseModel):
    id: int
    delivery_number: str
    order_id: int
    driver_id: int
    vehicle_id: int
    warehouse_id: int
    status: OrderStatus
    pickup_time: Optional[datetime] = None
    dispatched_at: datetime
    actual_delivery_time: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Embedded relationships if populated
    order: Optional[OrderResponse] = None
    status_history: List[DeliveryStatusHistoryResponse] = []

    model_config = ConfigDict(from_attributes=True)
