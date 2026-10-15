import math
import uuid
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.app.core.database import get_db
from backend.app.core.logger import logger
from backend.app.models.order import Order
from backend.app.models.package import Package
from backend.app.models.customer import Customer
from backend.app.models.warehouse import Warehouse
from backend.app.models.user import User
from backend.app.models.audit import AuditLog
from backend.app.models.enums import OrderStatus, UserRole
from backend.app.schemas.logistics import (
    OrderCreate,
    OrderStatusUpdate,
    OrderResponse,
    PackageResponse,
)
from backend.app.api.deps import (
    get_current_user,
    get_current_warehouse_manager,
)

router = APIRouter()


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points in kilometers."""
    R = 6371.0  # Earth radius in kilometers
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


def generate_order_number() -> str:
    """Generate unique order reference string: ORD-YYYYMMDD-XXXX."""
    date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
    unique_suffix = uuid.uuid4().hex[:6].upper()
    return f"ORD-{date_str}-{unique_suffix}"


def generate_tracking_number() -> str:
    """Generate package tracking string: TRK-XXXX-XXXX."""
    part1 = uuid.uuid4().hex[:4].upper()
    part2 = uuid.uuid4().hex[4:8].upper()
    return f"TRK-{part1}-{part2}"


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new order & package",
)
def create_order(
    data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Intake a new delivery order.
    Customers automatically create orders for their customer profile.
    Admins / Managers can specify customer_id.
    """
    # Resolve customer ID
    customer_id = data.customer_id
    if current_user.role == UserRole.CUSTOMER:
        cust = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not cust:
            # Auto-create basic customer profile if missing
            cust = Customer(
                user_id=current_user.id,
                company_name=current_user.full_name,
                country="India",
            )
            db.add(cust)
            db.flush()
        customer_id = cust.id
    else:
        if not customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="customer_id is required when creating an order as Admin/Manager",
            )
        cust = db.query(Customer).filter(Customer.id == customer_id).first()
        if not cust:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer ID {customer_id} does not exist",
            )

    # Calculate distance and initial estimated cost if warehouse specified
    est_distance = 0.0
    est_cost = 50.0  # Base delivery fee
    if data.warehouse_id:
        wh = db.query(Warehouse).filter(Warehouse.id == data.warehouse_id).first()
        if wh:
            est_distance = haversine_distance(
                wh.latitude, wh.longitude, data.destination_latitude, data.destination_longitude
            )
            # Cost model: Base (50) + 12 INR/km + 5 INR/kg
            est_cost = round(50.0 + (est_distance * 12.0) + (data.package.weight_kg * 5.0), 2)

    order_num = generate_order_number()
    new_order = Order(
        order_number=order_num,
        customer_id=customer_id,
        warehouse_id=data.warehouse_id,
        destination_address=data.destination_address.strip(),
        destination_city=data.destination_city.strip(),
        destination_state=data.destination_state.strip(),
        destination_postal_code=data.destination_postal_code.strip(),
        destination_latitude=data.destination_latitude,
        destination_longitude=data.destination_longitude,
        priority=data.priority,
        status=OrderStatus.CREATED,
        estimated_distance_km=est_distance,
        estimated_delivery_cost=est_cost,
        promised_delivery_time=data.promised_delivery_time,
    )
    db.add(new_order)
    db.flush()

    # Create associated package
    volume_m3 = round((data.package.length_cm * data.package.width_cm * data.package.height_cm) / 1000000.0, 4)
    tracking_num = generate_tracking_number()
    new_package = Package(
        order_id=new_order.id,
        tracking_number=tracking_num,
        weight_kg=data.package.weight_kg,
        length_cm=data.package.length_cm,
        width_cm=data.package.width_cm,
        height_cm=data.package.height_cm,
        volume_m3=volume_m3,
        category=data.package.category.strip().upper(),
        is_fragile=data.package.is_fragile,
        requires_cold_storage=data.package.requires_cold_storage,
        is_ready_for_dispatch=False,
    )
    db.add(new_package)
    db.flush()

    audit = AuditLog(
        user_id=current_user.id,
        action="ORDER_CREATE",
        resource_type="order",
        resource_id=str(new_order.id),
        details=f"Created order {new_order.order_number} with tracking {tracking_num}",
    )
    db.add(audit)
    db.commit()
    db.refresh(new_order)

    logger.info(f"Order created: {new_order.order_number} (Tracking: {tracking_num}) by User {current_user.id}")
    return new_order


@router.get(
    "",
    response_model=List[OrderResponse],
    summary="List orders",
)
def list_orders(
    status: Optional[OrderStatus] = Query(None, description="Filter by status"),
    warehouse_id: Optional[int] = Query(None, description="Filter by origin warehouse"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List orders. Customers view only their own orders; Admins & Managers view all.
    """
    query = db.query(Order)

    if current_user.role == UserRole.CUSTOMER:
        cust = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not cust:
            return []
        query = query.filter(Order.customer_id == cust.id)

    if status:
        query = query.filter(Order.status == status)
    if warehouse_id:
        query = query.filter(Order.warehouse_id == warehouse_id)

    return query.order_by(Order.id.desc()).all()


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order details",
)
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve order details with package specs.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order ID {order_id} not found",
        )

    # If customer, verify ownership
    if current_user.role == UserRole.CUSTOMER:
        cust = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not cust or order.customer_id != cust.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not own this order",
            )

    return order


@router.put(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Update order status",
)
def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    current_user: User = Depends(get_current_warehouse_manager),
    db: Session = Depends(get_db),
):
    """
    Update order status in warehouse processing lifecycle.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order ID {order_id} not found",
        )

    old_status = order.status
    order.status = data.status

    # If order set to READY_FOR_DISPATCH, mark package as ready
    if data.status == OrderStatus.READY_FOR_DISPATCH and order.package:
        order.package.is_ready_for_dispatch = True
        order.package.prepared_at = datetime.datetime.now(datetime.timezone.utc)

    audit = AuditLog(
        user_id=current_user.id,
        action="ORDER_STATUS_UPDATE",
        resource_type="order",
        resource_id=str(order.id),
        details=f"Status transition: {old_status.value} -> {data.status.value}. Reason: {data.reason or 'N/A'}",
    )
    db.add(audit)
    db.commit()
    db.refresh(order)

    return order


@router.get(
    "/track/{tracking_or_order_number}",
    summary="Public tracking endpoint by tracking number or order number",
)
def track_shipment(
    tracking_or_order_number: str,
    db: Session = Depends(get_db),
):
    """
    Public tracking query using tracking number (e.g. TRK-XXXX-XXXX) or order number (ORD-YYYYMMDD-XXXX).
    Provides customer-friendly timeline and status history.
    """
    identifier = tracking_or_order_number.strip().upper()

    order = (
        db.query(Order)
        .join(Package, Order.id == Package.order_id, isouter=True)
        .filter(
            or_(
                Order.order_number == identifier,
                Package.tracking_number == identifier,
            )
        )
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No shipment found matching reference '{tracking_or_order_number}'",
        )

    # Format delivery history if dispatched
    delivery_info = None
    timeline = []

    if order.delivery:
        delivery_info = {
            "delivery_number": order.delivery.delivery_number,
            "status": order.delivery.status.value,
            "dispatched_at": order.delivery.dispatched_at,
            "actual_delivery_time": order.delivery.actual_delivery_time,
            "driver_name": order.delivery.driver.user.full_name if order.delivery.driver and order.delivery.driver.user else "Assigned Fleet Driver",
            "vehicle_type": order.delivery.vehicle.vehicle_type.value if order.delivery.vehicle else None,
        }
        for h in order.delivery.status_history:
            timeline.append({
                "status": h.to_status.value,
                "timestamp": h.timestamp,
                "reason": h.reason,
                "notes": h.notes,
            })

    return {
        "order_number": order.order_number,
        "tracking_number": order.package.tracking_number if order.package else None,
        "status": order.status.value,
        "priority": order.priority.value,
        "destination_city": order.destination_city,
        "destination_postal_code": order.destination_postal_code,
        "estimated_distance_km": order.estimated_distance_km,
        "promised_delivery_time": order.promised_delivery_time,
        "package": {
            "weight_kg": order.package.weight_kg if order.package else None,
            "category": order.package.category if order.package else None,
            "is_fragile": order.package.is_fragile if order.package else False,
            "requires_cold_storage": order.package.requires_cold_storage if order.package else False,
        } if order.package else None,
        "delivery": delivery_info,
        "timeline": timeline,
    }
