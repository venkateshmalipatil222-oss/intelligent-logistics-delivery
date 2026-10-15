from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from backend.app.models.enums import DeliveryPriority, VehicleType


# -----------------------------------------------------------------------------
# Driver Assignment Intelligence Schemas
# -----------------------------------------------------------------------------
class ScoreBreakdown(BaseModel):
    proximity_score: float = Field(..., description="Proximity score (0-100), weight 35%")
    workload_score: float = Field(..., description="Workload score (0-100), weight 25%")
    performance_score: float = Field(..., description="Driver rating & reliability (0-100), weight 20%")
    vehicle_fit_score: float = Field(..., description="Vehicle type, efficiency & capacity fit (0-100), weight 20%")


class DriverCandidateEvaluation(BaseModel):
    driver_id: int
    user_id: int
    driver_name: str
    driver_phone: Optional[str] = None
    license_number: str
    current_status: str
    active_deliveries: int
    historical_rating: float
    vehicle_id: Optional[int] = None
    vehicle_registration: Optional[str] = None
    vehicle_type: Optional[str] = None
    distance_to_pickup_km: float
    is_eligible: bool
    rejection_reasons: List[str] = []
    total_score: float = Field(..., ge=0.0, le=100.0)
    score_breakdown: ScoreBreakdown
    recommendation_rank: int
    recommendation_rationale: str


class DriverAssignmentRecommendationResponse(BaseModel):
    order_id: int
    order_number: str
    pickup_warehouse_id: int
    pickup_warehouse_name: str
    package_weight_kg: float
    package_volume_m3: float
    evaluated_candidates_count: int
    eligible_candidates_count: int
    recommended_driver_id: Optional[int] = None
    candidates: List[DriverCandidateEvaluation]
    generated_at: datetime


class AutoAssignResultResponse(BaseModel):
    status: str
    message: str
    delivery_id: int
    delivery_number: str
    assigned_driver_id: int
    assigned_driver_name: str
    assigned_vehicle_registration: str
    otp_code: str
    match_score: float
    rationale: str


# -----------------------------------------------------------------------------
# Route Optimization Schemas
# -----------------------------------------------------------------------------
class RouteCoordinate(BaseModel):
    name: str
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)


class RouteLeg(BaseModel):
    leg_number: int
    origin_name: str
    origin_latitude: float
    origin_longitude: float
    destination_name: str
    destination_latitude: float
    destination_longitude: float
    distance_km: float
    estimated_time_minutes: float
    traffic_condition: str = "NORMAL"


class RouteOptimizationRequest(BaseModel):
    origin_latitude: float = Field(..., ge=-90.0, le=90.0)
    origin_longitude: float = Field(..., ge=-180.0, le=180.0)
    destination_latitude: float = Field(..., ge=-90.0, le=90.0)
    destination_longitude: float = Field(..., ge=-180.0, le=180.0)
    origin_name: Optional[str] = "Origin Depot"
    destination_name: Optional[str] = "Delivery Destination"


class RouteOptimizationResponse(BaseModel):
    origin: RouteCoordinate
    destination: RouteCoordinate
    straight_line_distance_km: float
    network_distance_km: float
    estimated_duration_minutes: float
    algorithm_used: str = "Dijkstra Waypoint Shortest Path"
    path_nodes: List[Dict[str, Any]]
    legs: List[RouteLeg]
    optimization_rationale: str


class StopPoint(BaseModel):
    id: str
    label: str
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    package_weight_kg: float = 0.0
    priority: DeliveryPriority = DeliveryPriority.MEDIUM


class MultiStopRouteRequest(BaseModel):
    depot_latitude: float = Field(..., ge=-90.0, le=90.0)
    depot_longitude: float = Field(..., ge=-180.0, le=180.0)
    depot_name: Optional[str] = "Central Warehouse Depot"
    stops: List[StopPoint] = Field(..., min_length=2)


class MultiStopRouteResponse(BaseModel):
    depot: RouteCoordinate
    total_stops: int
    total_route_distance_km: float
    estimated_total_duration_minutes: float
    savings_vs_unoptimized_km: float
    optimized_stop_sequence: List[StopPoint]
    route_legs: List[RouteLeg]
    algorithm_used: str = "Nearest-Neighbor TSP Heuristic"
    optimization_summary: str


# -----------------------------------------------------------------------------
# Transparent Cost Estimation Schemas
# -----------------------------------------------------------------------------
class CostLineItem(BaseModel):
    category: str
    label: str
    rate_basis: str
    quantity: float
    unit: str
    unit_cost_inr: float
    total_inr: float


class CostEstimationRequest(BaseModel):
    distance_km: float = Field(..., gt=0.0)
    package_weight_kg: float = Field(..., gt=0.0)
    package_volume_m3: float = Field(default=0.005, gt=0.0)
    vehicle_type: VehicleType = VehicleType.VAN
    fuel_efficiency_kmpl: Optional[float] = None
    priority: DeliveryPriority = DeliveryPriority.MEDIUM
    requires_cold_storage: bool = False


class CostEstimationResponse(BaseModel):
    distance_km: float
    package_weight_kg: float
    vehicle_type: str
    priority: str
    fuel_expense_inr: float
    driver_labor_inr: float
    vehicle_maintenance_inr: float
    dispatch_base_fee_inr: float
    priority_surcharge_inr: float
    cold_storage_surcharge_inr: float
    subtotal_inr: float
    tax_gst_inr: float  # 18% GST standard on freight logistics
    total_estimated_cost_inr: float
    line_items: List[CostLineItem]
    calculation_explanation: str
