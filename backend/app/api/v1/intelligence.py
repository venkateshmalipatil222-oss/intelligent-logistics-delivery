import uuid
import random
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.logger import logger
from backend.app.models.order import Order
from backend.app.models.delivery import Delivery, DeliveryStatusHistory
from backend.app.models.driver import Driver
from backend.app.models.warehouse import Warehouse
from backend.app.models.user import User
from backend.app.models.audit import AuditLog
from backend.app.models.enums import OrderStatus, DriverStatus, VehicleStatus
from backend.app.schemas.intelligence import (
    DriverAssignmentRecommendationResponse,
    AutoAssignResultResponse,
    RouteOptimizationRequest,
    RouteOptimizationResponse,
    MultiStopRouteRequest,
    MultiStopRouteResponse,
    CostEstimationRequest,
    CostEstimationResponse,
)
from backend.app.intelligence.assignment import DriverAssignmentEngine
from backend.app.intelligence.routing import RouteOptimizationEngine
from backend.app.intelligence.cost import CostEstimationEngine
from backend.app.api.deps import get_current_user, get_current_warehouse_manager

router = APIRouter()


@router.get(
    "/recommend-driver/{order_id}",
    response_model=DriverAssignmentRecommendationResponse,
    summary="Get intelligent driver recommendations for an order",
)
def recommend_driver_for_order(
    order_id: int,
    current_user: User = Depends(get_current_warehouse_manager),
    db: Session = Depends(get_db),
):
    """
    Evaluates all system drivers using multi-factor constraint satisfaction and scoring
    (proximity 35%, workload 25%, performance 20%, vehicle suitability 20%).
    Returns ranked candidate evaluations with transparent decision rationales.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order ID {order_id} not found",
        )

    try:
        recommendations = DriverAssignmentEngine.rank_drivers_for_order(db=db, order=order)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
    recommendations.generated_at = datetime.now(timezone.utc)
    return recommendations


@router.post(
    "/auto-assign/{order_id}",
    response_model=AutoAssignResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Auto-assign and dispatch order to top-ranked driver",
)
def auto_assign_driver(
    order_id: int,
    current_user: User = Depends(get_current_warehouse_manager),
    db: Session = Depends(get_db),
):
    """
    Runs multi-factor driver scoring and automatically dispatches the order to the #1
    eligible candidate, generating verification OTP and initializing operational tracking.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order ID {order_id} not found",
        )

    if order.status in [OrderStatus.DISPATCHED, OrderStatus.IN_TRANSIT, OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order {order.order_number} is already dispatched or delivered ({order.status.value})",
        )

    # Run ranking
    try:
        recommendations = DriverAssignmentEngine.rank_drivers_for_order(db=db, order=order)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
    if not recommendations.recommended_driver_id or recommendations.eligible_candidates_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No eligible driver found matching capacity, status, and workload constraints",
        )

    top_candidate = next(
        (c for c in recommendations.candidates if c.driver_id == recommendations.recommended_driver_id),
        None,
    )
    if not top_candidate:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve recommended driver details",
        )

    driver = db.query(Driver).filter(Driver.id == top_candidate.driver_id).first()
    warehouse = order.warehouse or db.query(Warehouse).filter(Warehouse.id == recommendations.pickup_warehouse_id).first()
    vehicle = driver.current_vehicle

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y%m%d")
    del_num = f"DEL-{date_str}-{uuid.uuid4().hex[:6].upper()}"
    otp = f"{random.randint(100000, 999999)}"

    # Create Delivery record
    delivery = Delivery(
        delivery_number=del_num,
        order_id=order.id,
        driver_id=driver.id,
        vehicle_id=vehicle.id,
        warehouse_id=warehouse.id,
        status=OrderStatus.DISPATCHED,
        pickup_time=now,
        dispatched_at=now,
        otp_code=otp,
    )
    db.add(delivery)
    db.flush()

    # Update states
    order.status = OrderStatus.DISPATCHED
    order.warehouse_id = warehouse.id

    driver.status = DriverStatus.BUSY
    driver.active_deliveries_count += 1
    vehicle.status = VehicleStatus.IN_SERVICE

    # Record dispatch status history
    history = DeliveryStatusHistory(
        delivery_id=delivery.id,
        from_status=None,
        to_status=OrderStatus.DISPATCHED,
        changed_by_user_id=current_user.id,
        reason=f"AI Auto-Assigned (Match Score: {top_candidate.total_score}%)",
        notes=f"Auto-selected #1 candidate {top_candidate.driver_name}. Rationale: {top_candidate.recommendation_rationale}",
        latitude=warehouse.latitude,
        longitude=warehouse.longitude,
        timestamp=now,
    )
    db.add(history)

    audit = AuditLog(
        user_id=current_user.id,
        action="AI_AUTO_ASSIGN_DISPATCH",
        resource_type="delivery",
        resource_id=str(delivery.id),
        details=f"Auto-assigned order {order.order_number} to driver {driver.license_number} with score {top_candidate.total_score}%",
    )
    db.add(audit)
    db.commit()

    logger.info(f"AI Auto-Assigned Order {order.order_number} -> Driver {driver.license_number} (Score: {top_candidate.total_score}%)")

    return AutoAssignResultResponse(
        status="success",
        message="Order successfully auto-assigned and dispatched",
        delivery_id=delivery.id,
        delivery_number=delivery.delivery_number,
        assigned_driver_id=driver.id,
        assigned_driver_name=top_candidate.driver_name,
        assigned_vehicle_registration=vehicle.registration_number,
        otp_code=otp,
        match_score=top_candidate.total_score,
        rationale=top_candidate.recommendation_rationale,
    )


@router.post(
    "/optimize-route",
    response_model=RouteOptimizationResponse,
    summary="Compute Dijkstra shortest path between coordinates",
)
def optimize_route(
    request: RouteOptimizationRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Executes Dijkstra Shortest-Path algorithm across modeled urban waypoint graph,
    returning turn-by-turn waypoint legs and travel duration estimations.
    """
    return RouteOptimizationEngine.calculate_dijkstra_route(
        orig_lat=request.origin_latitude,
        orig_lon=request.origin_longitude,
        dest_lat=request.destination_latitude,
        dest_lon=request.destination_longitude,
        orig_name=request.origin_name or "Origin",
        dest_name=request.destination_name or "Destination",
    )


@router.post(
    "/optimize-multi-stop",
    response_model=MultiStopRouteResponse,
    summary="Optimize multi-stop delivery route using Nearest-Neighbor TSP",
)
def optimize_multi_stop(
    request: MultiStopRouteRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Solves multi-drop route sequencing using Nearest-Neighbor TSP heuristic
    with priority bias, calculating distance savings vs unoptimized sequence.
    """
    return RouteOptimizationEngine.optimize_multi_stop_route(
        depot_lat=request.depot_latitude,
        depot_lon=request.depot_longitude,
        depot_name=request.depot_name or "Depot",
        stops=request.stops,
    )


@router.post(
    "/estimate-cost",
    response_model=CostEstimationResponse,
    summary="Estimate transparent itemized delivery costs",
)
def estimate_cost(
    request: CostEstimationRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Calculates transparent operating costs itemized by fuel/energy consumption,
    driver labor hours, fleet depreciation, priority surcharges, and GST.
    """
    return CostEstimationEngine.calculate_cost(request)
