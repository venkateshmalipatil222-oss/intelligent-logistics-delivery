from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.logger import logger
from backend.app.models.vehicle import Vehicle
from backend.app.models.user import User
from backend.app.models.audit import AuditLog
from backend.app.models.enums import VehicleStatus, VehicleType
from backend.app.schemas.logistics import (
    VehicleCreate,
    VehicleUpdate,
    VehicleResponse,
)
from backend.app.api.deps import (
    get_current_user,
    get_current_warehouse_manager,
)

router = APIRouter()


@router.get(
    "",
    response_model=List[VehicleResponse],
    summary="List all vehicles",
)
def list_vehicles(
    status: Optional[VehicleStatus] = Query(None, description="Filter by vehicle status"),
    vehicle_type: Optional[VehicleType] = Query(None, description="Filter by vehicle type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List fleet vehicles with status and type filters. Accessible to authenticated users.
    """
    query = db.query(Vehicle)
    if status:
        query = query.filter(Vehicle.status == status)
    if vehicle_type:
        query = query.filter(Vehicle.vehicle_type == vehicle_type)

    return query.order_by(Vehicle.id.asc()).all()


@router.get(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    summary="Get vehicle by ID",
)
def get_vehicle(
    vehicle_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve specific vehicle details.
    """
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with ID {vehicle_id} not found",
        )
    return vehicle


@router.post(
    "",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new fleet vehicle",
)
def create_vehicle(
    data: VehicleCreate,
    current_user: User = Depends(get_current_warehouse_manager),
    db: Session = Depends(get_db),
):
    """
    Register a new vehicle into the fleet. Restricted to Admin and Warehouse Manager.
    """
    reg_clean = data.registration_number.strip().upper()
    existing = db.query(Vehicle).filter(Vehicle.registration_number == reg_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Vehicle with registration '{reg_clean}' already exists",
        )

    new_vehicle = Vehicle(
        registration_number=reg_clean,
        model=data.model.strip(),
        vehicle_type=data.vehicle_type,
        max_weight_capacity_kg=data.max_weight_capacity_kg,
        max_volume_capacity_m3=data.max_volume_capacity_m3,
        fuel_type=data.fuel_type.strip(),
        fuel_efficiency_kmpl=data.fuel_efficiency_kmpl,
        status=data.status,
        current_latitude=data.current_latitude,
        current_longitude=data.current_longitude,
    )
    db.add(new_vehicle)
    db.flush()

    audit = AuditLog(
        user_id=current_user.id,
        action="VEHICLE_REGISTER",
        resource_type="vehicle",
        resource_id=str(new_vehicle.id),
        details=f"Registered vehicle {new_vehicle.registration_number} ({new_vehicle.model})",
    )
    db.add(audit)
    db.commit()
    db.refresh(new_vehicle)

    logger.info(f"Vehicle registered: ID {new_vehicle.id} ({new_vehicle.registration_number})")
    return new_vehicle


@router.put(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    summary="Update vehicle details",
)
def update_vehicle(
    vehicle_id: int,
    data: VehicleUpdate,
    current_user: User = Depends(get_current_warehouse_manager),
    db: Session = Depends(get_db),
):
    """
    Update vehicle specifications or operating status.
    """
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with ID {vehicle_id} not found",
        )

    update_fields = data.model_dump(exclude_unset=True)
    for field, val in update_fields.items():
        setattr(vehicle, field, val)

    audit = AuditLog(
        user_id=current_user.id,
        action="VEHICLE_UPDATE",
        resource_type="vehicle",
        resource_id=str(vehicle.id),
        details=f"Updated vehicle {vehicle.registration_number}: {list(update_fields.keys())}",
    )
    db.add(audit)
    db.commit()
    db.refresh(vehicle)

    return vehicle
