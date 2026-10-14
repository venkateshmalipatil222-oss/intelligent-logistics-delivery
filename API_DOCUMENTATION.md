# ILDO API Documentation & Reference

---

## 1. Authentication & Security Endpoints (`/api/v1/auth`)

### 1.1 Public Registration
- **Route:** `POST /api/v1/auth/register`
- **Access:** Public (Self-registration restricted to `CUSTOMER` and `DRIVER`)
- **Request Body:**
```json
{
  "email": "customer@ildo.com",
  "password": "SecurePassword123!",
  "full_name": "Rohan Sharma",
  "phone": "+919876543210",
  "role": "CUSTOMER",
  "company_name": "Apex Logistics",
  "address_line1": "45 MG Road",
  "city": "Bengaluru",
  "state": "Karnataka",
  "postal_code": "560001",
  "latitude": 12.9716,
  "longitude": 77.5946
}
```
- **Response (201 Created):**
```json
{
  "email": "customer@ildo.com",
  "full_name": "Rohan Sharma",
  "phone": "+919876543210",
  "role": "CUSTOMER",
  "id": 1,
  "is_active": true,
  "is_verified": false,
  "created_at": "2026-10-14T17:25:22.000Z",
  "customer": {
    "company_name": "Apex Logistics",
    "address_line1": "45 MG Road",
    "city": "Bengaluru",
    "state": "Karnataka",
    "postal_code": "560001",
    "country": "India",
    "default_latitude": 12.9716,
    "default_longitude": 77.5946,
    "id": 1,
    "user_id": 1
  }
}
```

---

### 1.2 User Login
- **Route:** `POST /api/v1/auth/login`
- **Access:** Public
- **Request Body:**
```json
{
  "email": "customer@ildo.com",
  "password": "SecurePassword123!"
}
```
- **Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "role": "CUSTOMER",
  "user_id": 1,
  "email": "customer@ildo.com",
  "full_name": "Rohan Sharma",
  "expires_in_seconds": 86400
}
```

---

### 1.3 Get Current User Profile
- **Route:** `GET /api/v1/auth/me`
- **Access:** Authenticated (Any active role)
- **Headers:** `Authorization: Bearer <JWT>`
- **Response (200 OK):** User and customer object.

---

### 1.4 Change Password
- **Route:** `POST /api/v1/auth/change-password`
- **Access:** Authenticated
- **Headers:** `Authorization: Bearer <JWT>`
- **Request Body:**
```json
{
  "current_password": "SecurePassword123!",
  "new_password": "NewUltraPassword456!"
}
```
- **Response (200 OK):**
```json
{
  "message": "Password updated successfully."
}
```

---

## 2. User Management Endpoints (`/api/v1/users`)

### 2.1 List All Users
- **Route:** `GET /api/v1/users`
- **Access:** `ADMIN` Only (Returns 403 Forbidden for non-admins)
- **Query Parameters:** `page=1&page_size=20&role=CUSTOMER&search=rohan`
- **Response (200 OK):**
```json
{
  "total": 1,
  "page": 1,
  "page_size": 20,
  "users": [...]
}
```

### 2.2 Security Audit Logs
- **Route:** `GET /api/v1/users/audit/logs`
- **Access:** `ADMIN` Only
- **Response (200 OK):** Array of security events with user ID, action code, timestamp, and IP address.
