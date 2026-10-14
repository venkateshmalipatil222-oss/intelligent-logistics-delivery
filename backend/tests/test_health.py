import pytest
from datetime import timedelta
import jwt
from backend.app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
)
from backend.app.core.config import settings


def test_root_endpoint(client):
    """Verify that root endpoint provides operational metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert data["service"] == settings.PROJECT_NAME
    assert "version" in data


def test_health_ping(client):
    """Verify the lightweight ping endpoint."""
    response = client.get("/api/v1/health/ping")
    assert response.status_code == 200
    data = response.json()
    assert data["ping"] == "pong"
    assert "timestamp" in data


def test_comprehensive_health(client):
    """Verify detailed health reporting with dependencies."""
    response = client.get("/api/v1/health")
    # In live test with database, status should be 200
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "dependencies" in data
    assert "database" in data["dependencies"]
    assert data["dependencies"]["database"]["status"] == "connected"
    assert "system" in data
    assert "process_time" in response.headers or "x-process-time" in response.headers


def test_password_hashing_and_verification():
    """Verify bcrypt password hashing, salting, and verification."""
    password = "SuperSecretPassword123!"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert hashed.startswith("$2b$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_token_lifecycle():
    """Verify JWT access token issuance, claims, and decoding."""
    subject = "user_42"
    role = "ADMIN"
    claims = {"email": "admin@ildo.local"}
    
    token = create_access_token(subject=subject, role=role, claims=claims, expires_delta=timedelta(minutes=15))
    assert isinstance(token, str)
    
    decoded = decode_access_token(token)
    assert decoded["sub"] == subject
    assert decoded["role"] == role
    assert decoded["email"] == "admin@ildo.local"
    assert "exp" in decoded
    assert "iat" in decoded


def test_jwt_token_invalid_signature():
    """Verify that tampered tokens fail validation."""
    token = create_access_token(subject="user_1", role="DRIVER")
    tampered_token = token[:-5] + "XXXXX"
    
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(tampered_token)
