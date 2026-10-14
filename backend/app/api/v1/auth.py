from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
)
from backend.app.core.logger import logger
from backend.app.models.user import User
from backend.app.models.customer import Customer
from backend.app.models.audit import AuditLog
from backend.app.models.enums import UserRole
from backend.app.schemas.auth import UserRegister, UserLogin, Token
from backend.app.schemas.user import UserResponse, PasswordChange
from backend.app.api.deps import get_current_user

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Public User Registration (Customer or Driver)"
)
def register(
    data: UserRegister,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Registers a new user account with hashed password and role validation.
    Prevents public privilege escalation to ADMIN or WAREHOUSE_MANAGER.
    Automatically creates a linked Customer record for customer accounts.
    """
    # Restrict public self-registration to CUSTOMER and DRIVER
    if data.role not in [UserRole.CUSTOMER, UserRole.DRIVER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Public registration is not permitted for role '{data.role.value}'. Contact administrator.",
        )

    # Check for existing user by email
    existing_user = db.query(User).filter(User.email == data.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    # Hash password safely using bcrypt
    hashed_pwd = get_password_hash(data.password)

    new_user = User(
        email=data.email.lower().strip(),
        hashed_password=hashed_pwd,
        full_name=data.full_name.strip(),
        phone=data.phone.strip() if data.phone else None,
        role=data.role,
        is_active=True,
        is_verified=False,
    )
    db.add(new_user)
    db.flush()  # Generates new_user.id for foreign key linkage

    # Create associated Customer profile if role is CUSTOMER
    if data.role == UserRole.CUSTOMER:
        customer_profile = Customer(
            user_id=new_user.id,
            company_name=data.company_name,
            address_line1=data.address_line1,
            city=data.city,
            state=data.state,
            postal_code=data.postal_code,
            country="India",
            default_latitude=data.latitude,
            default_longitude=data.longitude,
        )
        db.add(customer_profile)

    # Write audit log record
    client_ip = request.client.host if request.client else None
    audit = AuditLog(
        user_id=new_user.id,
        action="USER_REGISTER",
        resource_type="User",
        resource_id=str(new_user.id),
        details=f"User registered with role {data.role.value}",
        ip_address=client_ip,
    )
    db.add(audit)
    db.commit()
    db.refresh(new_user)

    logger.info(f"New user registered: ID {new_user.id} ({new_user.email}) as {new_user.role.value}")
    return new_user


@router.post(
    "/login",
    response_model=Token,
    summary="User Authentication and JWT Token Issuance"
)
def login(
    credentials: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Validates user credentials against stored bcrypt hash and returns a signed JWT access token.
    """
    user = db.query(User).filter(User.email == credentials.email.lower().strip()).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        logger.warning(f"Failed login attempt for email: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        logger.warning(f"Login rejected for inactive user ID: {user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact support.",
        )

    # Create JWT access token
    token_claims = {
        "email": user.email,
        "full_name": user.full_name,
    }
    expires_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    access_token = create_access_token(
        subject=user.id,
        role=user.role.value,
        claims=token_claims,
        expires_delta=timedelta(minutes=expires_minutes),
    )

    # Record login audit event
    client_ip = request.client.host if request.client else None
    audit = AuditLog(
        user_id=user.id,
        action="USER_LOGIN",
        resource_type="User",
        resource_id=str(user.id),
        details="Successful password authentication",
        ip_address=client_ip,
    )
    db.add(audit)
    db.commit()

    logger.info(f"User authenticated: ID {user.id} ({user.email}) [{user.role.value}]")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "expires_in_seconds": expires_minutes * 60,
    }


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current Authenticated User Profile"
)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns profile details of the currently authenticated user.
    """
    return current_user


@router.post(
    "/change-password",
    summary="Change Account Password"
)
def change_password(
    data: PasswordChange,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Verifies existing password and securely updates to a new bcrypt-hashed password.
    """
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The current password provided is incorrect.",
        )

    current_user.hashed_password = get_password_hash(data.new_password)
    
    # Audit log
    client_ip = request.client.host if request.client else None
    audit = AuditLog(
        user_id=current_user.id,
        action="PASSWORD_CHANGE",
        resource_type="User",
        resource_id=str(current_user.id),
        details="User updated their account password",
        ip_address=client_ip,
    )
    db.add(audit)
    db.commit()

    logger.info(f"Password changed for user ID: {current_user.id}")
    return {"message": "Password updated successfully."}
