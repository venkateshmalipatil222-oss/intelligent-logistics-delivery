from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.logger import logger
from backend.app.models.warehouse import Warehouse
from backend.app.models.user import User
from backend.app.models.audit import AuditLog
from backend.app.schemas.logistics import (
    WarehouseCreate,
    WarehouseUpdate,
    WarehouseResponse,
)
from backend.app.api.deps import (
    get_current_user,
    get_current_warehouse_manager,
    get_current_admin,
)

router = APIRouter()


@router.get(
    "",
    response_model=List[WarehouseResponse],
    summary="List all warehouses",
)
def list_warehouses(
    city: Optional[str] = Query(None, description="Filter by city name"),
    active_only: bool = Query(True, description="Only return active warehouses"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List warehouses with optional city filtering. Accessible to all authenticated users.
    """
    query = db.query(Warehouse)
    if active_only:
        query = query.filter(Warehouse.is_active == True)
    if city:
        query = query.filter(Warehouse.city.ilike(f"%{city.strip()}%"))

    return query.order_by(Warehouse.id.asc()).all()


@router.get(
    "/{warehouse_id}",
    response_model=WarehouseResponse,
    summary="Get warehouse by ID",
)
def get_warehouse(
    warehouse_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve specific warehouse details.
    """
    warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Warehouse with ID {warehouse_id} not found",
        )
    return warehouse


@router.post(
    "",
    response_model=WarehouseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new warehouse",
)
def create_warehouse(
    data: WarehouseCreate,
    current_user: User = Depends(get_current_warehouse_manager),
    db: Session = Depends(get_db),
):
    """
    Create a new warehouse. Restricted to Admin and Warehouse Manager.
    """
    existing = db.query(Warehouse).filter(Warehouse.code == data.code.strip().upper()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Warehouse code '{data.code}' already exists",
        )

    # If manager_id provided, verify user exists
    if data.manager_id:
        manager = db.query(User).filter(User.id == data.manager_id).first()
        if not manager:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Manager User ID {data.manager_id} not found",
            )

    new_warehouse = Warehouse(
        name=data.name.strip(),
        code=data.code.strip().upper(),
        address_line1=data.address_line1.strip(),
        city=data.city.strip(),
        state=data.state.strip(),
        postal_code=data.postal_code.strip(),
        latitude=data.latitude,
        longitude=data.longitude,
        capacity_sqft=data.capacity_sqft,
        contact_phone=data.contact_phone,
        manager_id=data.manager_id,
        is_active=data.is_active,
    )
    db.add(new_warehouse)
    db.flush()

    audit = AuditLog(
        user_id=current_user.id,
        action="WAREHOUSE_CREATE",
        resource_type="warehouse",
        resource_id=str(new_warehouse.id),
        details=f"Created warehouse {new_warehouse.name} ({new_warehouse.code})",
    )
    db.add(audit)
    db.commit()
    db.refresh(new_warehouse)

    logger.info(f"Warehouse created: ID {new_warehouse.id} ({new_warehouse.code}) by User {current_user.id}")
    return new_warehouse


@router.put(
    "/{warehouse_id}",
    response_model=WarehouseResponse,
    summary="Update an existing warehouse",
)
def update_warehouse(
    warehouse_id: int,
    data: WarehouseUpdate,
    current_user: User = Depends(get_current_warehouse_manager),
    db: Session = Depends(get_db),
):
    """
    Update warehouse parameters. Restricted to Admin and Warehouse Manager.
    """
    warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Warehouse with ID {warehouse_id} not found",
        )

    update_fields = data.model_dump(exclude_unset=True)
    for field, val in update_fields.items():
        setattr(warehouse, field, val)

    audit = AuditLog(
        user_id=current_user.id,
        action="WAREHOUSE_UPDATE",
        resource_type="warehouse",
        resource_id=str(warehouse.id),
        details=f"Updated warehouse {warehouse.code}: {list(update_fields.keys())}",
    )
    db.add(audit)
    db.commit()
    db.refresh(warehouse)

    return warehouse
