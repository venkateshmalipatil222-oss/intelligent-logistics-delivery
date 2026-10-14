from typing import List, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import decode_access_token
from backend.app.core.logger import logger
from backend.app.models.user import User
from backend.app.models.enums import UserRole

# OAuth2 token URL for Swagger UI authorization integration
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """
    Validates JWT token from Authorization header and retrieves authenticated User.
    Enforces that user exists and is active.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except (jwt.PyJWTError, ValueError) as exc:
        logger.warning(f"JWT validation failed: {exc}")
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive or suspended. Please contact administrator.",
        )
    return user


def require_roles(allowed_roles: List[UserRole]):
    """
    Dependency factory enforcing Role-Based Access Control (RBAC).
    Rejects any request from a user whose role is not within allowed_roles.
    """
    def role_verifier(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            logger.warning(
                f"RBAC Rejection: User {current_user.id} ({current_user.role.value}) "
                f"attempted to access endpoint restricted to {[r.value for r in allowed_roles]}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied: Insufficient permissions. Required role: "
                    f"{', '.join([r.value for r in allowed_roles])}. Your role: {current_user.role.value}"
                ),
            )
        return current_user

    return role_verifier


# Common role dependencies
get_current_admin = require_roles([UserRole.ADMIN])
get_current_warehouse_manager = require_roles([UserRole.ADMIN, UserRole.WAREHOUSE_MANAGER])
get_current_driver = require_roles([UserRole.ADMIN, UserRole.DRIVER])
get_current_customer = require_roles([UserRole.ADMIN, UserRole.CUSTOMER])
