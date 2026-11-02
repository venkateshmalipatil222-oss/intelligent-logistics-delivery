"""
Intelligent Optimization & Algorithmic Engines Package.
"""
from backend.app.intelligence.assignment import DriverAssignmentEngine, haversine_km
from backend.app.intelligence.routing import RouteOptimizationEngine, haversine_distance_km
from backend.app.intelligence.cost import CostEstimationEngine
from backend.app.intelligence.eta import DynamicETACalculator
from backend.app.intelligence.delay import DelayRiskDetector
from backend.app.intelligence.green_fleet import calculate_green_fleet_metrics
from backend.app.intelligence.geofence import evaluate_geofence_status, calculate_meters_distance

__all__ = [
    "DriverAssignmentEngine",
    "RouteOptimizationEngine",
    "CostEstimationEngine",
    "DynamicETACalculator",
    "DelayRiskDetector",
    "calculate_green_fleet_metrics",
    "evaluate_geofence_status",
    "calculate_meters_distance",
    "haversine_km",
    "haversine_distance_km",
]
