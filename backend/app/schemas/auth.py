from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from backend.app.models.enums import UserRole
from backend.app.schemas.user import UserResponse


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128, description="Must be at least 8 characters")
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    role: UserRole = Field(default=UserRole.CUSTOMER, description="Registration role (CUSTOMER or DRIVER)")
    
    # Optional customer location/address profile on registration
    company_name: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    user_id: int
    email: str
    full_name: str
    expires_in_seconds: int


class TokenPayload(BaseModel):
    sub: str
    role: UserRole
    exp: int
    iat: int


class AuthStatusResponse(BaseModel):
    authenticated: bool
    user: Optional[UserResponse] = None
