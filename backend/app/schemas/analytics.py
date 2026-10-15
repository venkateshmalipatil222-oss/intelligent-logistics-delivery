from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class FleetSummary(BaseModel):
    total_vehicles: int = 0
    active_vehicles: int = 0
    available_vehicles: int = 0
    in_maintenance_vehicles: int = 0
    ev_count: int = 0
    diesel_count: int = 0
    petrol_count: int = 0
    electric_percentage: float = 0.0


class DriverSummary(BaseModel):
    total_drivers: int = 0
    available_drivers: int = 0
    busy_drivers: int = 0
    offline_drivers: int = 0
    average_driver_rating: float = 5.0


class AnalyticsOverviewResponse(BaseModel):
    total_orders: int = 0
    total_deliveries: int = 0
    completed_deliveries: int = 0
    active_deliveries: int = 0
    failed_deliveries: int = 0
    sla_on_time_rate_pct: float = 100.0
    average_delivery_duration_minutes: float = 0.0
    total_revenue_inr: float = 0.0
    total_distance_km: float = 0.0
    order_status_distribution: Dict[str, int] = Field(default_factory=dict)
    delivery_status_distribution: Dict[str, int] = Field(default_factory=dict)
    priority_distribution: Dict[str, int] = Field(default_factory=dict)
    fleet_summary: FleetSummary
    driver_summary: DriverSummary
    failure_reasons_summary: Dict[str, int] = Field(default_factory=dict)
    generated_at: datetime


class DriverLeaderboardItem(BaseModel):
    rank: int
    driver_id: int
    user_id: int
    driver_name: str
    license_number: str
    phone: Optional[str] = None
    status: str
    rating: float
    total_deliveries_completed: int
    total_deliveries_failed: int
    active_deliveries_count: int
    on_time_rate_pct: float
    assigned_vehicle_registration: Optional[str] = None


class DriverLeaderboardResponse(BaseModel):
    total_ranked_drivers: int
    drivers: List[DriverLeaderboardItem]
    generated_at: datetime


class WarehouseUtilizationItem(BaseModel):
    warehouse_id: int
    warehouse_name: str
    warehouse_code: str
    city: str
    state: str
    capacity_sqft: float
    staged_packages_count: int
    processing_orders_count: int
    total_active_orders: int
    estimated_utilized_sqft: float
    utilization_rate_pct: float
    status_level: str  # NORMAL, ELEVATED, CRITICAL
    available_capacity_sqft: float


class WarehouseUtilizationResponse(BaseModel):
    total_warehouses: int
    warehouses: List[WarehouseUtilizationItem]
    total_network_capacity_sqft: float
    total_network_utilized_sqft: float
    average_utilization_rate_pct: float
    generated_at: datetime
