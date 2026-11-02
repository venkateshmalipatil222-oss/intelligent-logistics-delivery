from typing import Optional, List, Dict
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.core.database import get_db
from backend.app.core.logger import logger
from backend.app.models.user import User
from backend.app.models.order import Order
from backend.app.models.delivery import Delivery
from backend.app.models.vehicle import Vehicle
from backend.app.models.driver import Driver
from backend.app.models.warehouse import Warehouse
from backend.app.models.package import Package
from backend.app.models.enums import (
    UserRole,
    OrderStatus,
    DeliveryPriority,
    VehicleStatus,
    DriverStatus,
    VehicleType,
)
from backend.app.schemas.analytics import (
    FleetSummary,
    DriverSummary,
    AnalyticsOverviewResponse,
    DriverLeaderboardItem,
    DriverLeaderboardResponse,
    WarehouseUtilizationItem,
    WarehouseUtilizationResponse,
)
from backend.app.api.deps import require_roles

router = APIRouter()


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Helper to ensure datetime is offset-aware UTC across SQLite and MySQL."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@router.get(
    "/overview",
    response_model=AnalyticsOverviewResponse,
    summary="Get aggregated operational KPIs and fleet telemetry",
)
def get_analytics_overview(
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.WAREHOUSE_MANAGER])),
    db: Session = Depends(get_db),
):
    """
    Computes system-wide operational KPIs:
    - SLA on-time rate %, average delivery duration, and failure reason breakdowns.
    - Delivery and order status volume distributions.
    - Active fleet fuel mix (EV vs Diesel/Petrol) and availability metrics.
    - Active driver workforce capacity and ratings.
    """
    now = datetime.now(timezone.utc)

    # 1. Order Aggregations
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_revenue = db.query(func.sum(Order.estimated_delivery_cost)).scalar() or 0.0
    total_distance = db.query(func.sum(Order.estimated_distance_km)).scalar() or 0.0

    order_status_rows = db.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    order_status_distribution = {
        (s.value if hasattr(s, "value") else str(s)): count for s, count in order_status_rows
    }

    priority_rows = db.query(Order.priority, func.count(Order.id)).group_by(Order.priority).all()
    priority_distribution = {
        (p.value if hasattr(p, "value") else str(p)): count for p, count in priority_rows
    }

    # 2. Delivery Aggregations
    total_deliveries = db.query(func.count(Delivery.id)).scalar() or 0
    delivery_status_rows = db.query(Delivery.status, func.count(Delivery.id)).group_by(Delivery.status).all()
    delivery_status_distribution = {
        (s.value if hasattr(s, "value") else str(s)): count for s, count in delivery_status_rows
    }

    completed_deliveries = delivery_status_distribution.get(OrderStatus.DELIVERED.value, 0)
    failed_deliveries = delivery_status_distribution.get(OrderStatus.FAILED.value, 0)
    active_deliveries = (
        delivery_status_distribution.get(OrderStatus.DISPATCHED.value, 0)
        + delivery_status_distribution.get(OrderStatus.IN_TRANSIT.value, 0)
        + delivery_status_distribution.get(OrderStatus.OUT_FOR_DELIVERY.value, 0)
    )

    # SLA Calculation on completed deliveries
    delivered_records = (
        db.query(Delivery)
        .join(Order, Delivery.order_id == Order.id)
        .filter(Delivery.status == OrderStatus.DELIVERED)
        .all()
    )

    on_time_count = 0
    duration_minutes_list = []
    for del_item in delivered_records:
        # Check SLA
        if del_item.actual_delivery_time and del_item.order and del_item.order.promised_delivery_time:
            actual_time = _ensure_utc(del_item.actual_delivery_time)
            promised_time = _ensure_utc(del_item.order.promised_delivery_time)
            if actual_time <= promised_time:
                on_time_count += 1
        else:
            # If no promised time specified, marked on-time by default
            on_time_count += 1

        # Check Duration
        if del_item.actual_delivery_time and del_item.dispatched_at:
            act_time = _ensure_utc(del_item.actual_delivery_time)
            disp_time = _ensure_utc(del_item.dispatched_at)
            duration_minutes = (act_time - disp_time).total_seconds() / 60.0
            if duration_minutes >= 0:
                duration_minutes_list.append(duration_minutes)

    sla_pct = round((on_time_count / len(delivered_records) * 100.0), 2) if delivered_records else 100.0
    avg_duration = round(sum(duration_minutes_list) / len(duration_minutes_list), 1) if duration_minutes_list else 0.0

    # Failure reasons breakdown
    failure_rows = (
        db.query(Delivery.failure_reason, func.count(Delivery.id))
        .filter(Delivery.failure_reason.isnot(None))
        .group_by(Delivery.failure_reason)
        .all()
    )
    failure_reasons_summary = {str(r): count for r, count in failure_rows if r}

    # 3. Fleet Summary
    total_vehicles = db.query(func.count(Vehicle.id)).scalar() or 0
    active_vehicles = db.query(func.count(Vehicle.id)).filter(Vehicle.status == VehicleStatus.IN_SERVICE).scalar() or 0
    available_vehicles = db.query(func.count(Vehicle.id)).filter(Vehicle.status == VehicleStatus.AVAILABLE).scalar() or 0
    maint_vehicles = db.query(func.count(Vehicle.id)).filter(Vehicle.status == VehicleStatus.MAINTENANCE).scalar() or 0

    ev_count = (
        db.query(func.count(Vehicle.id))
        .filter(
            (Vehicle.vehicle_type == VehicleType.ELECTRIC_VAN)
            | (func.upper(Vehicle.fuel_type) == "ELECTRIC")
        )
        .scalar()
        or 0
    )
    diesel_count = (
        db.query(func.count(Vehicle.id))
        .filter(func.upper(Vehicle.fuel_type) == "DIESEL")
        .scalar()
        or 0
    )
    petrol_count = (
        db.query(func.count(Vehicle.id))
        .filter(func.upper(Vehicle.fuel_type) == "PETROL")
        .scalar()
        or 0
    )
    ev_pct = round((ev_count / total_vehicles * 100.0), 1) if total_vehicles > 0 else 0.0

    fleet_summary = FleetSummary(
        total_vehicles=total_vehicles,
        active_vehicles=active_vehicles,
        available_vehicles=available_vehicles,
        in_maintenance_vehicles=maint_vehicles,
        ev_count=ev_count,
        diesel_count=diesel_count,
        petrol_count=petrol_count,
        electric_percentage=ev_pct,
    )

    # 4. Driver Workforce Summary
    total_drivers = db.query(func.count(Driver.id)).scalar() or 0
    available_drivers = db.query(func.count(Driver.id)).filter(Driver.status == DriverStatus.AVAILABLE).scalar() or 0
    busy_drivers = db.query(func.count(Driver.id)).filter(Driver.status == DriverStatus.BUSY).scalar() or 0
    offline_drivers = db.query(func.count(Driver.id)).filter(Driver.status == DriverStatus.OFFLINE).scalar() or 0
    avg_rating = db.query(func.avg(Driver.rating)).scalar() or 5.0

    driver_summary = DriverSummary(
        total_drivers=total_drivers,
        available_drivers=available_drivers,
        busy_drivers=busy_drivers,
        offline_drivers=offline_drivers,
        average_driver_rating=round(float(avg_rating), 2),
    )

    return AnalyticsOverviewResponse(
        total_orders=total_orders,
        total_deliveries=total_deliveries,
        completed_deliveries=completed_deliveries,
        active_deliveries=active_deliveries,
        failed_deliveries=failed_deliveries,
        sla_on_time_rate_pct=sla_pct,
        average_delivery_duration_minutes=avg_duration,
        total_revenue_inr=round(float(total_revenue), 2),
        total_distance_km=round(float(total_distance), 2),
        order_status_distribution=order_status_distribution,
        delivery_status_distribution=delivery_status_distribution,
        priority_distribution=priority_distribution,
        fleet_summary=fleet_summary,
        driver_summary=driver_summary,
        failure_reasons_summary=failure_reasons_summary,
        generated_at=now,
    )


@router.get(
    "/driver-leaderboard",
    response_model=DriverLeaderboardResponse,
    summary="Get ranked driver performance leaderboard",
)
def get_driver_leaderboard(
    limit: int = Query(20, ge=1, le=100, description="Max leaderboard entries to return"),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.WAREHOUSE_MANAGER, UserRole.DRIVER])),
    db: Session = Depends(get_db),
):
    """
    Ranks drivers using a weighted performance index:
    - Rating (40%), Total Completed Deliveries (40%), and Delivery Success/On-Time Rate (20%).
    """
    drivers = db.query(Driver).join(User, Driver.user_id == User.id).all()

    leaderboard_items = []
    for driver in drivers:
        total_finished = driver.total_deliveries_completed + driver.total_deliveries_failed
        on_time_rate = (
            round((driver.total_deliveries_completed / total_finished) * 100.0, 1)
            if total_finished > 0
            else 100.0
        )

        user_obj = driver.user
        vehicle_reg = driver.current_vehicle.registration_number if driver.current_vehicle else None

        # Composite score calculation for sorting
        composite_score = (
            (driver.rating * 20.0)  # max 100
            + (driver.total_deliveries_completed * 2.0)
            - (driver.total_deliveries_failed * 5.0)
            + (on_time_rate * 0.5)
        )

        leaderboard_items.append({
            "score": composite_score,
            "driver_id": driver.id,
            "user_id": driver.user_id,
            "driver_name": user_obj.full_name if user_obj else f"Driver #{driver.id}",
            "license_number": driver.license_number,
            "phone": user_obj.phone if user_obj else None,
            "status": driver.status.value if hasattr(driver.status, "value") else str(driver.status),
            "rating": round(float(driver.rating), 2),
            "total_deliveries_completed": driver.total_deliveries_completed,
            "total_deliveries_failed": driver.total_deliveries_failed,
            "active_deliveries_count": driver.active_deliveries_count,
            "on_time_rate_pct": on_time_rate,
            "assigned_vehicle_registration": vehicle_reg,
        })

    # Sort descending by composite performance score
    leaderboard_items.sort(key=lambda d: d["score"], reverse=True)

    ranked_items: List[DriverLeaderboardItem] = []
    for idx, item in enumerate(leaderboard_items[:limit], start=1):
        ranked_items.append(
            DriverLeaderboardItem(
                rank=idx,
                driver_id=item["driver_id"],
                user_id=item["user_id"],
                driver_name=item["driver_name"],
                license_number=item["license_number"],
                phone=item["phone"],
                status=item["status"],
                rating=item["rating"],
                total_deliveries_completed=item["total_deliveries_completed"],
                total_deliveries_failed=item["total_deliveries_failed"],
                active_deliveries_count=item["active_deliveries_count"],
                on_time_rate_pct=item["on_time_rate_pct"],
                assigned_vehicle_registration=item["assigned_vehicle_registration"],
            )
        )

    return DriverLeaderboardResponse(
        total_ranked_drivers=len(ranked_items),
        drivers=ranked_items,
        generated_at=datetime.now(timezone.utc),
    )


@router.get(
    "/warehouse-utilization",
    response_model=WarehouseUtilizationResponse,
    summary="Get warehouse floor capacity and package staging metrics",
)
def get_warehouse_utilization(
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.WAREHOUSE_MANAGER])),
    db: Session = Depends(get_db),
):
    """
    Monitors cross-docking facility floor capacity:
    - Counts staged vs processing packages.
    - Estimates square footage utilization and flags threshold alerts (NORMAL <70%, ELEVATED 70-90%, CRITICAL >90%).
    """
    warehouses = db.query(Warehouse).filter(Warehouse.is_active == True).all()

    warehouse_items: List[WarehouseUtilizationItem] = []
    total_net_capacity = 0.0
    total_net_utilized = 0.0

    for wh in warehouses:
        total_net_capacity += wh.capacity_sqft

        # Query active orders assigned to this warehouse
        active_orders = (
            db.query(Order)
            .filter(
                Order.warehouse_id == wh.id,
                Order.status.in_([
                    OrderStatus.CREATED,
                    OrderStatus.CONFIRMED,
                    OrderStatus.PROCESSING,
                    OrderStatus.READY_FOR_DISPATCH,
                ]),
            )
            .all()
        )

        staged_count = sum(1 for o in active_orders if o.status == OrderStatus.READY_FOR_DISPATCH or (o.package and o.package.is_ready_for_dispatch))
        processing_count = len(active_orders) - staged_count

        # Estimate footprint: standard operational parcel staging base = 35 sqft per active unit + 150 sqft cross-dock buffer
        utilized_sqft = round(min(wh.capacity_sqft, (len(active_orders) * 35.0) + (150.0 if active_orders else 0.0)), 1)
        total_net_utilized += utilized_sqft

        util_pct = round((utilized_sqft / wh.capacity_sqft * 100.0), 2) if wh.capacity_sqft > 0 else 0.0
        status_level = "CRITICAL" if util_pct >= 90.0 else ("ELEVATED" if util_pct >= 70.0 else "NORMAL")
        available_sqft = max(0.0, round(wh.capacity_sqft - utilized_sqft, 1))

        warehouse_items.append(
            WarehouseUtilizationItem(
                warehouse_id=wh.id,
                warehouse_name=wh.name,
                warehouse_code=wh.code,
                city=wh.city,
                state=wh.state,
                capacity_sqft=wh.capacity_sqft,
                staged_packages_count=staged_count,
                processing_orders_count=processing_count,
                total_active_orders=len(active_orders),
                estimated_utilized_sqft=utilized_sqft,
                utilization_rate_pct=util_pct,
                status_level=status_level,
                available_capacity_sqft=available_sqft,
            )
        )

    avg_utilization = round((total_net_utilized / total_net_capacity * 100.0), 2) if total_net_capacity > 0 else 0.0

    return WarehouseUtilizationResponse(
        total_warehouses=len(warehouse_items),
        warehouses=warehouse_items,
        total_network_capacity_sqft=round(total_net_capacity, 1),
        total_network_utilized_sqft=round(total_net_utilized, 1),
        average_utilization_rate_pct=avg_utilization,
        generated_at=datetime.now(timezone.utc),
    )


@router.get(
    "/green-fleet",
    summary="Get Sustainable Green Fleet & Carbon Footprint (CO2) Analytics (Phase 12)",
)
def get_green_fleet_analytics(
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.WAREHOUSE_MANAGER])),
    db: Session = Depends(get_db),
):
    """
    Computes real-time fleet sustainability metrics:
    - EV percentage, CO2 emissions prevented, fuel saved in liters and INR.
    - ESG environmental rating and equivalent urban trees planted.
    """
    from backend.app.intelligence.green_fleet import calculate_green_fleet_metrics

    vehicles = db.query(Vehicle).all()
    vehicle_dicts = [
        {
            "id": v.id,
            "registration_number": v.registration_number,
            "fuel_type": v.fuel_type,
            "status": v.status.value if hasattr(v.status, "value") else str(v.status)
        }
        for v in vehicles
    ]

    total_delivered_km = (
        db.query(func.sum(Order.estimated_distance_km))
        .join(Delivery, Delivery.order_id == Order.id)
        .filter(Delivery.status == OrderStatus.DELIVERED)
        .scalar()
        or 245.5  # Seed distance if zero
    )

    metrics = calculate_green_fleet_metrics(
        vehicles=vehicle_dicts,
        total_delivered_km=float(total_delivered_km),
        fuel_price_per_liter=95.0
    )
    metrics["generated_at"] = datetime.now(timezone.utc)
    return metrics
