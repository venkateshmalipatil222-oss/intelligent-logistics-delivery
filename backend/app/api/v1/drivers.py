from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from backend.app.core.database import get_db
from backend.app.core.logger import logger
from backend.app.models.driver import Driver
from backend.app.models.vehicle import Vehicle
from backend.app.models.user import User
from backend.app.models.audit import AuditLog
from backend.app.models.enums import DriverStatus, VehicleStatus, UserRole
from backend.app.schemas.logistics import (
    DriverCreate,
    DriverUpdate,
    DriverLocationUpdate,
    DriverResponse,
)
from backend.app.api.deps import (
    get_current_user,
    get_current_warehouse_manager,
    get_current_driver,
)

router = APIRouter()


def _format_driver_response(driver: Driver) -> dict:
    """Helper formatting Driver model into DriverResponse dict with relation fields."""
    return {
        "id": driver.id,
        "user_id": driver.user_id,
        "license_number": driver.license_number,
        "current_vehicle_id": driver.current_vehicle_id,
        "status": driver.status,
        "current_latitude": driver.current_latitude,
        "current_longitude": driver.current_longitude,
        "last_location_updated_at": driver.last_location_updated_at,
        "total_deliveries_completed": driver.total_deliveries_completed,
        "total_deliveries_failed": driver.total_deliveries_failed,
        "rating": driver.rating,
        "active_deliveries_count": driver.active_deliveries_count,
        "created_at": driver.created_at,
        "updated_at": driver.updated_at,
        "driver_name": driver.user.full_name if driver.user else None,
        "driver_email": driver.user.email if driver.user else None,
        "driver_phone": driver.user.phone if driver.user else None,
        "vehicle_registration": driver.current_vehicle.registration_number if driver.current_vehicle else None,
    }


@router.get(
    "",
    response_model=List[DriverResponse],
    summary="List all drivers",
)
def list_drivers(
    status: Optional[DriverStatus] = Query(None, description="Filter by driver status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List drivers with optional status filtering.
    """
    query = db.query(Driver)
    if status:
        query = query.filter(Driver.status == status)

    drivers = query.order_by(Driver.id.asc()).all()
    return [_format_driver_response(d) for d in drivers]


@router.get(
    "/me",
    response_model=DriverResponse,
    summary="Get current driver profile",
)
def get_driver_me(
    current_user: User = Depends(get_current_driver),
    db: Session = Depends(get_db),
):
    """
    Get profile for currently authenticated driver.
    """
    driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver profile not found for current user account",
        )
    return _format_driver_response(driver)


@router.get(
    "/{driver_id}",
    response_model=DriverResponse,
    summary="Get driver by ID",
)
def get_driver(
    driver_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve specific driver profile.
    """
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver with ID {driver_id} not found",
        )
    return _format_driver_response(driver)


@router.post(
    "",
    response_model=DriverResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new driver",
)
def create_driver(
    data: DriverCreate,
    current_user: User = Depends(get_current_warehouse_manager),
    db: Session = Depends(get_db),
):
    """
    Create a new driver profile linked to a user account with DRIVER role.
    """
    # Verify user exists and has DRIVER or ADMIN role
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User ID {data.user_id} not found",
        )
    if user.role not in [UserRole.DRIVER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User {user.email} has role {user.role.value}. Expected DRIVER.",
        )

    # Check if driver profile already exists for user
    existing_user_driver = db.query(Driver).filter(Driver.user_id == data.user_id).first()
    if existing_user_driver:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Driver profile already exists for this user",
        )

    # Check license uniqueness
    lic_clean = data.license_number.strip().upper()
    existing_lic = db.query(Driver).filter(Driver.license_number == lic_clean).first()
    if existing_lic:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Driver with license number '{lic_clean}' already registered",
        )

    # Verify vehicle if assigned
    if data.current_vehicle_id:
        vehicle = db.query(Vehicle).filter(Vehicle.id == data.current_vehicle_id).first()
        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vehicle ID {data.current_vehicle_id} not found",
            )
        vehicle.status = VehicleStatus.ASSIGNED

    new_driver = Driver(
        user_id=data.user_id,
        license_number=lic_clean,
        current_vehicle_id=data.current_vehicle_id,
        status=data.status,
    )
    db.add(new_driver)
    db.flush()

    audit = AuditLog(
        user_id=current_user.id,
        action="DRIVER_REGISTER",
        resource_type="driver",
        resource_id=str(new_driver.id),
        details=f"Registered driver {new_driver.license_number} for user {user.email}",
    )
    db.add(audit)
    db.commit()
    db.refresh(new_driver)

    logger.info(f"Driver registered: ID {new_driver.id} (User {user.email})")
    return _format_driver_response(new_driver)


@router.put(
    "/{driver_id}",
    response_model=DriverResponse,
    summary="Update driver profile",
)
def update_driver(
    driver_id: int,
    data: DriverUpdate,
    current_user: User = Depends(get_current_warehouse_manager),
    db: Session = Depends(get_db),
):
    """
    Update driver details, status, or assigned vehicle.
    """
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver with ID {driver_id} not found",
        )

    update_fields = data.model_dump(exclude_unset=True)
    if "license_number" in update_fields:
        driver.license_number = update_fields["license_number"].strip().upper()

    if "current_vehicle_id" in update_fields:
        new_v_id = update_fields["current_vehicle_id"]
        if new_v_id != driver.current_vehicle_id:
            # Free old vehicle
            if driver.current_vehicle_id:
                old_v = db.query(Vehicle).filter(Vehicle.id == driver.current_vehicle_id).first()
                if old_v:
                    old_v.status = VehicleStatus.AVAILABLE
            # Assign new vehicle
            if new_v_id:
                new_v = db.query(Vehicle).filter(Vehicle.id == new_v_id).first()
                if not new_v:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Vehicle ID {new_v_id} not found",
                    )
                new_v.status = VehicleStatus.ASSIGNED
            driver.current_vehicle_id = new_v_id

    if "status" in update_fields:
        driver.status = update_fields["status"]

    db.commit()
    db.refresh(driver)
    return _format_driver_response(driver)


@router.post(
    "/location",
    summary="Update driver real-time GPS location",
)
def update_driver_location(
    data: DriverLocationUpdate,
    current_user: User = Depends(get_current_driver),
    db: Session = Depends(get_db),
):
    """
    Updates driver's real-time latitude & longitude coordinates.
    Also updates linked vehicle coordinates if assigned.
    """
    driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver profile not found for current user",
        )

    now = datetime.now(timezone.utc)
    driver.current_latitude = data.latitude
    driver.current_longitude = data.longitude
    driver.last_location_updated_at = now

    if driver.current_vehicle_id:
        vehicle = db.query(Vehicle).filter(Vehicle.id == driver.current_vehicle_id).first()
        if vehicle:
            vehicle.current_latitude = data.latitude
            vehicle.current_longitude = data.longitude

    db.commit()

    return {
        "status": "success",
        "driver_id": driver.id,
        "latitude": data.latitude,
        "longitude": data.longitude,
        "timestamp": now.isoformat(),
    }
