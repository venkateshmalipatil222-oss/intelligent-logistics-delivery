import pytest
from backend.app.models.user import User
from backend.app.models.enums import UserRole
from backend.app.core.security import get_password_hash, create_access_token


def test_customer_registration(client, db_session):
    """Verify customer registration creates user and customer profile, hashes password."""
    payload = {
        "email": "customer1@ildo.com",
        "password": "Password123!",
        "full_name": "Test Customer",
        "phone": "+919876543210",
        "role": "CUSTOMER",
        "company_name": "Acme Deliveries",
        "city": "Bengaluru",
        "state": "Karnataka",
        "postal_code": "560001",
        "latitude": 12.9716,
        "longitude": 77.5946,
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "customer1@ildo.com"
    assert data["role"] == "CUSTOMER"
    assert data["is_active"] is True
    assert "hashed_password" not in data  # Never expose password hash

    # Verify database state
    user_in_db = db_session.query(User).filter(User.email == "customer1@ildo.com").first()
    assert user_in_db is not None
    assert user_in_db.hashed_password != "Password123!"  # Passwords must not be plaintext
    assert user_in_db.hashed_password.startswith("$2b$")
    assert user_in_db.customer is not None
    assert user_in_db.customer.city == "Bengaluru"


def test_driver_registration(client, db_session):
    """Verify driver registration is permitted publicly."""
    payload = {
        "email": "driver1@ildo.com",
        "password": "SecureDriverPassword123!",
        "full_name": "Rajesh Kumar",
        "phone": "+919876543211",
        "role": "DRIVER",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "driver1@ildo.com"
    assert data["role"] == "DRIVER"


def test_reject_public_admin_registration(client):
    """Verify that public registration rejects self-escalation to ADMIN."""
    payload = {
        "email": "fakeadmin@ildo.com",
        "password": "Password123!",
        "full_name": "Rogue Admin",
        "role": "ADMIN",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 403
    assert "Public registration is not permitted" in response.json()["detail"]


def test_duplicate_email_registration(client):
    """Verify duplicate email registration is rejected with 400 Bad Request."""
    payload = {
        "email": "dup@ildo.com",
        "password": "Password123!",
        "full_name": "User One",
        "role": "CUSTOMER",
    }
    resp1 = client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == 201

    resp2 = client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == 400
    assert "already exists" in resp2.json()["detail"]


def test_login_success(client, db_session):
    """Verify authentication with valid credentials returns a signed JWT."""
    pwd = "ValidPassword123!"
    user = User(
        email="auth_user@ildo.com",
        hashed_password=get_password_hash(pwd),
        full_name="Auth User",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "auth_user@ildo.com", "password": pwd},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "CUSTOMER"
    assert data["user_id"] == user.id
    assert data["email"] == "auth_user@ildo.com"


def test_login_invalid_password(client, db_session):
    """Verify authentication with wrong password returns 401 Unauthorized."""
    user = User(
        email="user_pwd@ildo.com",
        hashed_password=get_password_hash("CorrectPassword123!"),
        full_name="User Pwd",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user_pwd@ildo.com", "password": "WrongPassword!"},
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_login_inactive_user(client, db_session):
    """Verify login for deactivated account is rejected with 403 Forbidden."""
    user = User(
        email="deactivated@ildo.com",
        hashed_password=get_password_hash("Password123!"),
        full_name="Inactive User",
        role=UserRole.CUSTOMER,
        is_active=False,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "deactivated@ildo.com", "password": "Password123!"},
    )
    assert response.status_code == 403
    assert "deactivated" in response.json()["detail"]


def test_get_me_endpoint(client, db_session):
    """Verify /api/v1/auth/me returns current user profile with valid Bearer token."""
    user = User(
        email="me_test@ildo.com",
        hashed_password=get_password_hash("Password123!"),
        full_name="Me Tester",
        role=UserRole.DRIVER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(subject=user.id, role=user.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user.id
    assert data["email"] == "me_test@ildo.com"
    assert data["role"] == "DRIVER"


def test_rbac_admin_endpoint_protection(client, db_session):
    """
    CRITICAL RBAC TEST:
    Verify non-admin (Customer, Driver) cannot access /api/v1/users (returns 403 Forbidden).
    Verify Admin can access /api/v1/users (returns 200 OK).
    """
    customer = User(
        email="cust_rbac@ildo.com",
        hashed_password=get_password_hash("Password123!"),
        full_name="Customer RBAC",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    admin = User(
        email="admin_rbac@ildo.com",
        hashed_password=get_password_hash("AdminPassword123!"),
        full_name="Admin RBAC",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add_all([customer, admin])
    db_session.commit()

    cust_token = create_access_token(subject=customer.id, role=customer.role.value)
    admin_token = create_access_token(subject=admin.id, role=admin.role.value)

    # Customer attempts to list users -> 403 Forbidden
    cust_resp = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {cust_token}"}
    )
    assert cust_resp.status_code == 403
    assert "Access denied" in cust_resp.json()["detail"]

    # Admin attempts to list users -> 200 OK
    admin_resp = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert admin_resp.status_code == 200
    data = admin_resp.json()
    assert "users" in data
    assert data["total"] >= 2


def test_change_password(client, db_session):
    """Verify password change workflow."""
    old_pwd = "OldPassword123!"
    new_pwd = "NewPassword123!"
    user = User(
        email="pwd_change@ildo.com",
        hashed_password=get_password_hash(old_pwd),
        full_name="Password Changer",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token(subject=user.id, role=user.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Attempt with wrong current password -> 400 Bad Request
    fail_resp = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "WrongOldPassword!", "new_password": new_pwd},
        headers=headers,
    )
    assert fail_resp.status_code == 400

    # 2. Attempt with correct current password -> 200 OK
    success_resp = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": old_pwd, "new_password": new_pwd},
        headers=headers,
    )
    assert success_resp.status_code == 200

    # 3. Verify user can now login with new password
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "pwd_change@ildo.com", "password": new_pwd},
    )
    assert login_resp.status_code == 200
