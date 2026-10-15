import math
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.app.models.driver import Driver
from backend.app.models.order import Order
from backend.app.models.warehouse import Warehouse
from backend.app.models.vehicle import Vehicle
from backend.app.models.enums import DriverStatus, VehicleStatus, VehicleType
from backend.app.schemas.intelligence import (
    DriverCandidateEvaluation,
    ScoreBreakdown,
    DriverAssignmentRecommendationResponse,
)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on Earth in kilometers."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


class DriverAssignmentEngine:
    """
    Multi-Factor Driver Scoring and Intelligent Assignment Engine.
    Evaluates candidate drivers using strict constraint satisfaction followed
    by weighted multi-criteria decision analysis (MCDA).
    """

    # Scoring weights (sum = 1.0)
    WEIGHT_PROXIMITY = 0.35
    WEIGHT_WORKLOAD = 0.25
    WEIGHT_PERFORMANCE = 0.20
    WEIGHT_VEHICLE_FIT = 0.20

    MAX_CONCURRENT_DELIVERIES = 3

    @classmethod
    def evaluate_driver(
        cls,
        driver: Driver,
        order: Order,
        warehouse: Warehouse,
    ) -> Tuple[bool, List[str], float, ScoreBreakdown, str]:
        """
        Evaluates a single driver candidate against order requirements.
        Returns: (is_eligible, rejection_reasons, total_score, score_breakdown, rationale)
        """
        rejection_reasons = []

        # -------------------------------------------------------------
        # 1. HARD CONSTRAINT VERIFICATION
        # -------------------------------------------------------------
        # Constraint A: Driver Status
        if driver.status in [DriverStatus.OFFLINE, DriverStatus.UNAVAILABLE]:
            rejection_reasons.append(f"Driver is currently {driver.status.value}")

        # Constraint B: Vehicle Assignment
        vehicle = driver.current_vehicle
        if not vehicle:
            rejection_reasons.append("Driver has no assigned vehicle")
        elif vehicle.status == VehicleStatus.MAINTENANCE:
            rejection_reasons.append(f"Assigned vehicle {vehicle.registration_number} is under maintenance")

        # Constraint C: Capacity Verification
        pkg_weight = order.package.weight_kg if order.package else 5.0
        pkg_volume = order.package.volume_m3 if order.package else 0.01

        if vehicle:
            if pkg_weight > vehicle.max_weight_capacity_kg:
                rejection_reasons.append(
                    f"Package weight ({pkg_weight} kg) exceeds vehicle payload limit ({vehicle.max_weight_capacity_kg} kg)"
                )
            if pkg_volume > vehicle.max_volume_capacity_m3:
                rejection_reasons.append(
                    f"Package volume ({pkg_volume} m³) exceeds vehicle volume limit ({vehicle.max_volume_capacity_m3} m³)"
                )

        # Constraint D: Workload saturation
        if driver.active_deliveries_count >= cls.MAX_CONCURRENT_DELIVERIES:
            rejection_reasons.append(
                f"Driver has reached maximum active deliveries limit ({driver.active_deliveries_count}/{cls.MAX_CONCURRENT_DELIVERIES})"
            )

        is_eligible = len(rejection_reasons) == 0

        # -------------------------------------------------------------
        # 2. SOFT MULTI-FACTOR SCORING (Normalized 0.0 - 100.0)
        # -------------------------------------------------------------
        # Factor 1: Proximity to pickup warehouse (Weight: 35%)
        # If driver has no live GPS, fallback to warehouse coordinate distance
        drv_lat = driver.current_latitude if driver.current_latitude is not None else warehouse.latitude
        drv_lon = driver.current_longitude if driver.current_longitude is not None else warehouse.longitude
        distance_to_pickup = haversine_km(drv_lat, drv_lon, warehouse.latitude, warehouse.longitude)

        # Linear decay: 100 at 0km, decays by 3.0 pts per km, 0 at >= 33.3km
        proximity_score = max(0.0, min(100.0, 100.0 - (distance_to_pickup * 3.0)))

        # Factor 2: Workload distribution (Weight: 25%)
        # 0 active -> 100, 1 active -> 65, 2 active -> 30, >=3 -> 0
        workload_score = max(0.0, min(100.0, 100.0 - (driver.active_deliveries_count * 35.0)))

        # Factor 3: Driver Performance & Rating (Weight: 20%)
        # Rating 0-5 scaled to 0-100 (60% weight) + Completion rate (40% weight)
        total_finished = driver.total_deliveries_completed + driver.total_deliveries_failed
        completion_rate = (
            (driver.total_deliveries_completed / total_finished) if total_finished > 0 else 0.95
        )
        rating_score = (driver.rating / 5.0) * 100.0
        performance_score = round((0.6 * rating_score) + (0.4 * (completion_rate * 100.0)), 2)

        # Factor 4: Vehicle Suitability & Eco-Efficiency (Weight: 20%)
        vehicle_fit_score = 50.0  # Base
        if vehicle:
            # Eco bonus for electric vehicles
            if vehicle.vehicle_type == VehicleType.ELECTRIC_VAN or "ELECTRIC" in vehicle.fuel_type.upper():
                vehicle_fit_score += 20.0
            # Sizing optimization
            if pkg_weight <= 20.0 and vehicle.vehicle_type == VehicleType.BIKE:
                vehicle_fit_score += 25.0
            elif 20.0 < pkg_weight <= 800.0 and vehicle.vehicle_type in [VehicleType.VAN, VehicleType.ELECTRIC_VAN]:
                vehicle_fit_score += 25.0
            elif pkg_weight > 800.0 and vehicle.vehicle_type == VehicleType.TRUCK:
                vehicle_fit_score += 25.0
            else:
                vehicle_fit_score += 10.0
        vehicle_fit_score = min(100.0, vehicle_fit_score)

        breakdown = ScoreBreakdown(
            proximity_score=round(proximity_score, 2),
            workload_score=round(workload_score, 2),
            performance_score=round(performance_score, 2),
            vehicle_fit_score=round(vehicle_fit_score, 2),
        )

        if not is_eligible:
            total_score = 0.0
            rationale = f"Ineligible for assignment: {'; '.join(rejection_reasons)}."
        else:
            total_score = round(
                (cls.WEIGHT_PROXIMITY * proximity_score)
                + (cls.WEIGHT_WORKLOAD * workload_score)
                + (cls.WEIGHT_PERFORMANCE * performance_score)
                + (cls.WEIGHT_VEHICLE_FIT * vehicle_fit_score),
                2,
            )
            vehicle_desc = f"{vehicle.registration_number} ({vehicle.model})" if vehicle else "No vehicle"
            rationale = (
                f"Scored {total_score}/100. Distance to pickup: {distance_to_pickup} km "
                f"(proximity score: {breakdown.proximity_score}), active deliveries: {driver.active_deliveries_count}, "
                f"rating: {driver.rating}⭐, vehicle: {vehicle_desc}."
            )

        return is_eligible, rejection_reasons, total_score, breakdown, rationale

    @classmethod
    def rank_drivers_for_order(
        cls,
        db: Session,
        order: Order,
    ) -> DriverAssignmentRecommendationResponse:
        """
        Evaluates and ranks all drivers in the system for a given order.
        """
        warehouse = order.warehouse
        if not warehouse:
            # Default to first active warehouse if order has none set
            warehouse = db.query(Warehouse).filter(Warehouse.is_active == True).first()
            if not warehouse:
                raise ValueError("No active warehouse found to calculate pickup proximity.")

        drivers = db.query(Driver).all()
        evaluations: List[DriverCandidateEvaluation] = []

        for d in drivers:
            is_elig, rejections, score, breakdown, rationale = cls.evaluate_driver(
                driver=d,
                order=order,
                warehouse=warehouse,
            )
            driver_name = d.user.full_name if d.user else f"Driver #{d.id}"
            driver_phone = d.user.phone if d.user else None

            # Calculate distance
            drv_lat = d.current_latitude if d.current_latitude is not None else warehouse.latitude
            drv_lon = d.current_longitude if d.current_longitude is not None else warehouse.longitude
            dist = haversine_km(drv_lat, drv_lon, warehouse.latitude, warehouse.longitude)

            evaluations.append(
                DriverCandidateEvaluation(
                    driver_id=d.id,
                    user_id=d.user_id,
                    driver_name=driver_name,
                    driver_phone=driver_phone,
                    license_number=d.license_number,
                    current_status=d.status.value,
                    active_deliveries=d.active_deliveries_count,
                    historical_rating=d.rating,
                    vehicle_id=d.current_vehicle_id,
                    vehicle_registration=d.current_vehicle.registration_number if d.current_vehicle else None,
                    vehicle_type=d.current_vehicle.vehicle_type.value if d.current_vehicle else None,
                    distance_to_pickup_km=dist,
                    is_eligible=is_elig,
                    rejection_reasons=rejections,
                    total_score=score,
                    score_breakdown=breakdown,
                    recommendation_rank=0,  # Assigned after sort
                    recommendation_rationale=rationale,
                )
            )

        # Sort: eligible first, then descending total score, then ascending distance
        evaluations.sort(
            key=lambda x: (1 if x.is_eligible else 0, x.total_score, -x.distance_to_pickup_km),
            reverse=True,
        )

        # Assign ranks
        for idx, item in enumerate(evaluations, start=1):
            item.recommendation_rank = idx

        eligible_count = sum(1 for e in evaluations if e.is_eligible)
        recommended_id = evaluations[0].driver_id if eligible_count > 0 else None

        return DriverAssignmentRecommendationResponse(
            order_id=order.id,
            order_number=order.order_number,
            pickup_warehouse_id=warehouse.id,
            pickup_warehouse_name=warehouse.name,
            package_weight_kg=order.package.weight_kg if order.package else 0.0,
            package_volume_m3=order.package.volume_m3 if order.package else 0.0,
            evaluated_candidates_count=len(evaluations),
            eligible_candidates_count=eligible_count,
            recommended_driver_id=recommended_id,
            candidates=evaluations,
            generated_at=warehouse.created_at,  # Or current timestamp
        )
