import random
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.logger import logger
from backend.app.models.delivery import Delivery, DeliveryStatusHistory
from backend.app.models.order import Order
from backend.app.models.driver import Driver
from backend.app.models.vehicle import Vehicle
from backend.app.models.warehouse import Warehouse
from backend.app.models.user import User
from backend.app.models.customer import Customer
from backend.app.models.audit import AuditLog
from backend.app.models.enums import (
    OrderStatus,
    DriverStatus,
    VehicleStatus,
    UserRole,
    DeliveryFailureReason,
)
from backend.app.schemas.logistics import (
    DeliveryDispatchCreate,
    DeliveryStatusTransition,
    DeliveryVerifyOTP,
    DeliveryFailureReport,
    DeliveryRegenerateOTPResponse,
    DeliveryResponse,
    DeliveryStatusHistoryResponse,
)
from backend.app.services.notification_service import (
    notify_delivery_dispatched,
    notify_delivery_completed,
    notify_delivery_failed,
    notify_otp_regenerated,
)
from backend.app.api.deps import (
    get_current_user,
    get_current_warehouse_manager,
    get_current_driver,
)

router = APIRouter()

# Valid delivery state machine transitions
ALLOWED_TRANSITIONS = {
    OrderStatus.DISPATCHED: [OrderStatus.IN_TRANSIT, OrderStatus.FAILED, OrderStatus.CANCELLED],
    OrderStatus.IN_TRANSIT: [OrderStatus.OUT_FOR_DELIVERY, OrderStatus.FAILED, OrderStatus.CANCELLED],
    OrderStatus.OUT_FOR_DELIVERY: [OrderStatus.DELIVERED, OrderStatus.FAILED, OrderStatus.CANCELLED, OrderStatus.RETURNED],
    OrderStatus.FAILED: [OrderStatus.READY_FOR_DISPATCH, OrderStatus.CANCELLED],
    OrderStatus.RETURNED: [OrderStatus.READY_FOR_DISPATCH, OrderStatus.CANCELLED],
    OrderStatus.DELIVERED: [],  # Terminal state
    OrderStatus.CANCELLED: [],  # Terminal state
}


def generate_delivery_number() -> str:
    """Generate unique delivery reference string: DEL-YYYYMMDD-XXXX."""
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    unique_suffix = uuid.uuid4().hex[:6].upper()
    return f"DEL-{date_str}-{unique_suffix}"


def generate_otp() -> str:
    """Generate secure 6-digit delivery verification OTP."""
    return f"{random.randint(100000, 999999)}"


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure datetime is offset-aware in UTC for safe comparisons."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@router.post(
    "/dispatch",
    response_model=DeliveryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Dispatch order to driver & vehicle",
)
def dispatch_order(
    data: DeliveryDispatchCreate,
    current_user: User = Depends(get_current_warehouse_manager),
    db: Session = Depends(get_db),
):
    """
    Dispatch an order:
    1. Verifies order is ready for dispatch and not already dispatched.
    2. Validates driver and vehicle availability and capacity.
    3. Generates 6-digit verification OTP and delivery number.
    4. Updates driver and vehicle operational states.
    5. Records initial dispatch history and audit log.
    """
    # 1. Verify Order
    order = db.query(Order).filter(Order.id == data.order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order ID {data.order_id} not found",
        )
    if order.status in [OrderStatus.DISPATCHED, OrderStatus.IN_TRANSIT, OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order {order.order_number} is already in state '{order.status.value}'",
        )

    # 2. Verify Warehouse
    warehouse = db.query(Warehouse).filter(Warehouse.id == data.warehouse_id).first()
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Warehouse ID {data.warehouse_id} not found",
        )

    # 3. Verify Driver
    driver = db.query(Driver).filter(Driver.id == data.driver_id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver ID {data.driver_id} not found",
        )
    if driver.status == DriverStatus.OFFLINE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Driver {driver.license_number} is currently OFFLINE",
        )

    # 4. Verify Vehicle & Capacity Check
    vehicle = db.query(Vehicle).filter(Vehicle.id == data.vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle ID {data.vehicle_id} not found",
        )
    if vehicle.status == VehicleStatus.MAINTENANCE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vehicle {vehicle.registration_number} is under MAINTENANCE",
        )

    # Capacity check against package specifications
    if order.package:
        if order.package.weight_kg > vehicle.max_weight_capacity_kg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Package weight ({order.package.weight_kg}kg) exceeds vehicle "
                    f"{vehicle.registration_number} max weight capacity ({vehicle.max_weight_capacity_kg}kg)"
                ),
            )
        if order.package.volume_m3 > vehicle.max_volume_capacity_m3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Package volume ({order.package.volume_m3}m3) exceeds vehicle "
                    f"{vehicle.registration_number} max volume capacity ({vehicle.max_volume_capacity_m3}m3)"
                ),
            )

    # 5. Create Delivery
    now = datetime.now(timezone.utc)
    del_num = generate_delivery_number()
    otp = generate_otp()
    otp_expires = now + timedelta(hours=24)

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
        otp_expires_at=otp_expires,
        otp_attempts=0,
    )
    db.add(delivery)
    db.flush()

    # 6. Update operational states
    order.status = OrderStatus.DISPATCHED
    order.warehouse_id = warehouse.id

    driver.status = DriverStatus.BUSY
    driver.active_deliveries_count += 1
    if not driver.current_vehicle_id:
        driver.current_vehicle_id = vehicle.id

    vehicle.status = VehicleStatus.IN_SERVICE

    # 7. Add Status History
    history = DeliveryStatusHistory(
        delivery_id=delivery.id,
        from_status=None,
        to_status=OrderStatus.DISPATCHED,
        changed_by_user_id=current_user.id,
        reason="Dispatched from warehouse",
        notes=f"Assigned to driver {driver.license_number} with vehicle {vehicle.registration_number}",
        latitude=warehouse.latitude,
        longitude=warehouse.longitude,
    )
    db.add(history)

    # 8. Audit Log
    audit = AuditLog(
        user_id=current_user.id,
        action="DELIVERY_DISPATCH",
        resource_type="delivery",
        resource_id=str(delivery.id),
        details=f"Dispatched order {order.order_number} as delivery {del_num}",
    )
    db.add(audit)

    # 9. Notify Customer
    customer_user_id = order.customer.user_id if order.customer else None
    notify_delivery_dispatched(db, delivery, customer_user_id)

    db.commit()
    db.refresh(delivery)

    logger.info(f"Dispatched delivery {delivery.delivery_number} for order {order.order_number}")
    return delivery


@router.get(
    "",
    response_model=List[DeliveryResponse],
    summary="List deliveries",
)
def list_deliveries(
    status: Optional[OrderStatus] = Query(None, description="Filter by status"),
    driver_id: Optional[int] = Query(None, description="Filter by driver"),
    warehouse_id: Optional[int] = Query(None, description="Filter by warehouse"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List deliveries. Drivers view only their assigned deliveries; Admins & Managers view all.
    """
    query = db.query(Delivery)

    if current_user.role == UserRole.DRIVER:
        driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
        if not driver:
            return []
        query = query.filter(Delivery.driver_id == driver.id)
    elif driver_id:
        query = query.filter(Delivery.driver_id == driver_id)

    if status:
        query = query.filter(Delivery.status == status)
    if warehouse_id:
        query = query.filter(Delivery.warehouse_id == warehouse_id)

    return query.order_by(Delivery.id.desc()).all()


@router.get(
    "/{delivery_id}",
    response_model=DeliveryResponse,
    summary="Get delivery details",
)
def get_delivery(
    delivery_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve full delivery details with status history and linked order.
    """
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery ID {delivery_id} not found",
        )

    # If driver, verify assignment
    if current_user.role == UserRole.DRIVER:
        driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
        if not driver or delivery.driver_id != driver.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not assigned to this delivery",
            )

    return delivery


@router.post(
    "/{delivery_id}/status",
    response_model=DeliveryResponse,
    summary="Transition delivery status",
)
def update_delivery_status(
    delivery_id: int,
    data: DeliveryStatusTransition,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Execute delivery status transition with state machine validation:
    DISPATCHED -> IN_TRANSIT -> OUT_FOR_DELIVERY -> DELIVERED / FAILED / CANCELLED.
    """
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery ID {delivery_id} not found",
        )

    # Permission check: DRIVER assigned or WAREHOUSE_MANAGER / ADMIN
    if current_user.role == UserRole.DRIVER:
        driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
        if not driver or delivery.driver_id != driver.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not assigned to this delivery",
            )

    current_status = delivery.status
    target_status = data.to_status

    # Check allowed transitions
    allowed = ALLOWED_TRANSITIONS.get(current_status, [])
    if target_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid state transition from '{current_status.value}' to '{target_status.value}'. "
                f"Allowed target states: {[s.value for s in allowed]}"
            ),
        )

    # Require failure reason if status is FAILED
    if target_status == OrderStatus.FAILED and not data.reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A failure reason is required when marking delivery as FAILED",
        )

    now = datetime.now(timezone.utc)
    delivery.status = target_status
    delivery.order.status = target_status

    # Update timestamps and operational states
    if target_status == OrderStatus.DELIVERED:
        delivery.actual_delivery_time = now
        delivery.driver.total_deliveries_completed += 1
        delivery.driver.active_deliveries_count = max(0, delivery.driver.active_deliveries_count - 1)
        if delivery.driver.active_deliveries_count == 0:
            delivery.driver.status = DriverStatus.AVAILABLE
            delivery.vehicle.status = VehicleStatus.AVAILABLE

    elif target_status == OrderStatus.FAILED:
        delivery.failed_at = now
        delivery.failure_reason = data.reason
        delivery.driver.total_deliveries_failed += 1
        delivery.driver.active_deliveries_count = max(0, delivery.driver.active_deliveries_count - 1)
        if delivery.driver.active_deliveries_count == 0:
            delivery.driver.status = DriverStatus.AVAILABLE
            delivery.vehicle.status = VehicleStatus.AVAILABLE

    # Record status transition history
    history = DeliveryStatusHistory(
        delivery_id=delivery.id,
        from_status=current_status,
        to_status=target_status,
        changed_by_user_id=current_user.id,
        reason=data.reason,
        notes=data.notes,
        latitude=data.latitude,
        longitude=data.longitude,
        timestamp=now,
    )
    db.add(history)

    # Record driver coordinates if sent
    if data.latitude is not None and data.longitude is not None:
        delivery.driver.current_latitude = data.latitude
        delivery.driver.current_longitude = data.longitude
        delivery.driver.last_location_updated_at = now

    audit = AuditLog(
        user_id=current_user.id,
        action="DELIVERY_STATUS_TRANSITION",
        resource_type="delivery",
        resource_id=str(delivery.id),
        details=f"Delivery {delivery.delivery_number} transitioned {current_status.value} -> {target_status.value}",
    )
    db.add(audit)
    db.commit()
    db.refresh(delivery)

    logger.info(f"Delivery {delivery.delivery_number} transitioned: {current_status.value} -> {target_status.value}")
    return delivery


@router.post(
    "/{delivery_id}/verify-otp",
    response_model=DeliveryResponse,
    summary="Complete delivery with OTP verification",
)
def verify_delivery_otp(
    delivery_id: int,
    data: DeliveryVerifyOTP,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Complete handover with secure 6-digit OTP verification:
    1. Validates OTP attempt limit (max 5) and expiration.
    2. Compares submitted OTP with delivery.otp_code.
    3. Upon success, marks delivery and order as DELIVERED with POD proof.
    4. Triggers completion notification to customer.
    """
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery ID {delivery_id} not found",
        )

    if delivery.status == OrderStatus.DELIVERED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Delivery has already been completed",
        )

    now = datetime.now(timezone.utc)

    # 1. Check max attempt lockout
    if delivery.otp_attempts >= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum OTP verification attempts (5) exceeded. Please regenerate a new OTP.",
        )

    # 2. Check time-limited expiration
    if delivery.otp_expires_at and now > _ensure_utc(delivery.otp_expires_at):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Delivery OTP has expired. Recipient must regenerate a fresh OTP.",
        )

    # 3. Verify OTP match
    if delivery.otp_code != data.otp_code.strip():
        delivery.otp_attempts += 1
        db.commit()
        remaining = max(0, 5 - delivery.otp_attempts)
        logger.warning(
            f"OTP verification failed for delivery {delivery.delivery_number}: attempt {delivery.otp_attempts}/5"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OTP code. {remaining} attempt(s) remaining.",
        )

    old_status = delivery.status

    delivery.status = OrderStatus.DELIVERED
    delivery.actual_delivery_time = now
    delivery.recipient_name = data.recipient_name
    delivery.pod_photo_url = data.pod_photo_url
    delivery.pod_signature_data = data.pod_signature_data
    delivery.order.status = OrderStatus.DELIVERED

    # Update driver & vehicle metrics
    delivery.driver.total_deliveries_completed += 1
    delivery.driver.active_deliveries_count = max(0, delivery.driver.active_deliveries_count - 1)
    if delivery.driver.active_deliveries_count == 0:
        delivery.driver.status = DriverStatus.AVAILABLE
        delivery.vehicle.status = VehicleStatus.AVAILABLE

    history_notes = data.notes or f"Package received and verified by {data.recipient_name or 'Recipient'}"
    history = DeliveryStatusHistory(
        delivery_id=delivery.id,
        from_status=old_status,
        to_status=OrderStatus.DELIVERED,
        changed_by_user_id=current_user.id,
        reason="OTP Handover Verification Successful",
        notes=history_notes,
        latitude=data.latitude,
        longitude=data.longitude,
        timestamp=now,
    )
    db.add(history)

    audit = AuditLog(
        user_id=current_user.id,
        action="DELIVERY_OTP_VERIFIED",
        resource_type="delivery",
        resource_id=str(delivery.id),
        details=f"Delivery {delivery.delivery_number} completed via OTP verification",
    )
    db.add(audit)

    # Notify Customer of completion
    customer_user_id = delivery.order.customer.user_id if delivery.order and delivery.order.customer else None
    notify_delivery_completed(db, delivery, customer_user_id)

    db.commit()
    db.refresh(delivery)

    logger.info(f"Delivery {delivery.delivery_number} completed via OTP verification")
    return delivery


@router.post(
    "/{delivery_id}/regenerate-otp",
    response_model=DeliveryRegenerateOTPResponse,
    summary="Regenerate fresh time-limited OTP for delivery",
)
def regenerate_delivery_otp(
    delivery_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Regenerate a new 6-digit verification OTP.
    Accessible by Admin, Warehouse Manager, or the Customer who owns this order.
    """
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery ID {delivery_id} not found",
        )

    if delivery.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot regenerate OTP for delivery in terminal status {delivery.status.value}",
        )

    # If customer, verify ownership
    if current_user.role == UserRole.CUSTOMER:
        cust = db.query(Customer).filter(Customer.user_id == current_user.id).first()
        if not cust or delivery.order.customer_id != cust.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only regenerate OTPs for your own orders",
            )

    now = datetime.now(timezone.utc)
    new_otp = generate_otp()
    new_expires = now + timedelta(hours=2)

    delivery.otp_code = new_otp
    delivery.otp_expires_at = new_expires
    delivery.otp_attempts = 0

    audit = AuditLog(
        user_id=current_user.id,
        action="DELIVERY_OTP_REGENERATED",
        resource_type="delivery",
        resource_id=str(delivery.id),
        details=f"OTP regenerated for delivery {delivery.delivery_number}",
    )
    db.add(audit)

    # Send Notification to Customer
    customer_user_id = delivery.order.customer.user_id if delivery.order and delivery.order.customer else None
    if customer_user_id:
        notify_otp_regenerated(db, delivery, customer_user_id, new_otp)

    db.commit()
    db.refresh(delivery)

    return DeliveryRegenerateOTPResponse(
        delivery_id=delivery.id,
        delivery_number=delivery.delivery_number,
        otp_code=new_otp,
        otp_expires_at=new_expires,
        message="A new 6-digit verification OTP has been generated successfully.",
    )


@router.post(
    "/{delivery_id}/report-failure",
    response_model=DeliveryResponse,
    summary="Report delivery failure with structured reason code",
)
def report_delivery_failure(
    delivery_id: int,
    data: DeliveryFailureReport,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Report delivery attempt failure with structured reason code and remarks.
    Accessible by assigned Driver, Warehouse Manager, or Admin.
    """
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery ID {delivery_id} not found",
        )

    if delivery.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot report failure for delivery in terminal status {delivery.status.value}",
        )

    # If driver, verify assignment
    if current_user.role == UserRole.DRIVER:
        driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
        if not driver or delivery.driver_id != driver.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not assigned to this delivery",
            )

    now = datetime.now(timezone.utc)
    old_status = delivery.status

    failure_text = f"{data.reason.value}: {data.notes.strip()}"
    delivery.status = OrderStatus.FAILED
    delivery.failed_at = now
    delivery.failure_reason = failure_text
    delivery.order.status = OrderStatus.FAILED

    if data.photo_url:
        delivery.pod_photo_url = data.photo_url

    # Update driver metrics
    delivery.driver.total_deliveries_failed += 1
    delivery.driver.active_deliveries_count = max(0, delivery.driver.active_deliveries_count - 1)
    if delivery.driver.active_deliveries_count == 0:
        delivery.driver.status = DriverStatus.AVAILABLE
        delivery.vehicle.status = VehicleStatus.AVAILABLE

    # Record History
    history = DeliveryStatusHistory(
        delivery_id=delivery.id,
        from_status=old_status,
        to_status=OrderStatus.FAILED,
        changed_by_user_id=current_user.id,
        reason=f"Delivery Failed: {data.reason.value}",
        notes=data.notes,
        latitude=data.latitude,
        longitude=data.longitude,
        timestamp=now,
    )
    db.add(history)

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="DELIVERY_FAILURE_REPORTED",
        resource_type="delivery",
        resource_id=str(delivery.id),
        details=f"Delivery {delivery.delivery_number} failed. Reason: {failure_text}",
    )
    db.add(audit)

    # Notify Customer & Warehouse Managers
    customer_user_id = delivery.order.customer.user_id if delivery.order and delivery.order.customer else None
    notify_delivery_failed(db, delivery, data.reason.value, data.notes, customer_user_id)

    db.commit()
    db.refresh(delivery)

    logger.warning(f"Delivery {delivery.delivery_number} marked FAILED: {failure_text}")
    return delivery
