from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.app.core.database import get_db
from backend.app.core.logger import logger
from backend.app.models.user import User
from backend.app.models.audit import AuditLog
from backend.app.models.enums import UserRole
from backend.app.schemas.user import UserResponse, UserListResponse, UserUpdate
from backend.app.api.deps import get_current_user, get_current_admin

router = APIRouter()


@router.get(
    "",
    response_model=UserListResponse,
    summary="List Users (Admin Only)"
)
def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    role: Optional[UserRole] = Query(None, description="Filter by user role"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Retrieves paginated users with optional role filtering and search. Restricted to ADMIN.
    """
    query = db.query(User)

    if role:
        query = query.filter(User.role == role)

    if search:
        search_fmt = f"%{search.strip()}%"
        query = query.filter(
            or_(
                User.full_name.ilike(search_fmt),
                User.email.ilike(search_fmt),
            )
        )

    total = query.count()
    users = (
        query.order_by(User.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "users": users,
    }


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get User By ID"
)
def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves user profile. Users can only access their own profile unless they have ADMIN role.
    """
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this user's profile.",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found.",
        )
    return user


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update User Profile / Status"
)
def update_user(
    user_id: int,
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Updates user details. Only ADMIN can modify account activation status (`is_active`).
    """
    # Only Admin or the account owner can edit
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to modify this user account.",
        )

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found.",
        )

    if update_data.full_name is not None:
        target_user.full_name = update_data.full_name.strip()
    if update_data.phone is not None:
        target_user.phone = update_data.phone.strip()

    # Only ADMIN can change is_active
    if update_data.is_active is not None:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can activate or deactivate accounts.",
            )
        target_user.is_active = update_data.is_active

    db.commit()
    db.refresh(target_user)
    logger.info(f"User ID {user_id} updated by user ID {current_user.id}")
    return target_user


@router.get(
    "/audit/logs",
    summary="View Security Audit Logs (Admin Only)"
)
def get_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Lists system security and operational audit logs. Restricted to ADMIN.
    """
    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return logs
