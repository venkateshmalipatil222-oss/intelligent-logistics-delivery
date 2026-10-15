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

### 1.3 Get Current User Profile
- **Route:** `GET /api/v1/auth/me`
- **Access:** Authenticated (Any active role)

### 1.4 Change Password
- **Route:** `POST /api/v1/auth/change-password`
- **Access:** Authenticated

---

## 2. Warehouses (`/api/v1/warehouses`)

### 2.1 List Warehouses
- **Route:** `GET /api/v1/warehouses?city=Bengaluru&active_only=true`
- **Access:** Authenticated (All Roles)

### 2.2 Create Warehouse
- **Route:** `POST /api/v1/warehouses`
- **Access:** `ADMIN`, `WAREHOUSE_MANAGER`
- **Request Body:**
```json
{
  "name": "Bengaluru Central Logistics Hub",
  "code": "WH-BLR-01",
  "address_line1": "Plot 12, Industrial Area, Peenya",
  "city": "Bengaluru",
  "state": "Karnataka",
  "postal_code": "560058",
  "latitude": 13.0285,
  "longitude": 77.5197,
  "capacity_sqft": 50000.0,
  "contact_phone": "+918023456789"
}
```

### 2.3 Get Warehouse Detail / Update
- **Route:** `GET /api/v1/warehouses/{id}`, `PUT /api/v1/warehouses/{id}`
- **Access:** `ADMIN`, `WAREHOUSE_MANAGER`

---

## 3. Fleet & Vehicles (`/api/v1/vehicles`)

### 3.1 List Vehicles
- **Route:** `GET /api/v1/vehicles?status=AVAILABLE&vehicle_type=ELECTRIC_VAN`
- **Access:** Authenticated

### 3.2 Register Vehicle
- **Route:** `POST /api/v1/vehicles`
- **Access:** `ADMIN`, `WAREHOUSE_MANAGER`
- **Request Body:**
```json
{
  "registration_number": "KA-01-EV-2024",
  "model": "Tata Ace EV",
  "vehicle_type": "ELECTRIC_VAN",
  "max_weight_capacity_kg": 1000.0,
  "max_volume_capacity_m3": 5.8,
  "fuel_type": "ELECTRIC",
  "fuel_efficiency_kmpl": 16.5,
  "status": "AVAILABLE"
}
```

---

## 4. Drivers (`/api/v1/drivers`)

### 4.1 List Drivers
- **Route:** `GET /api/v1/drivers?status=AVAILABLE`
- **Access:** Authenticated

### 4.2 Current Driver Profile
- **Route:** `GET /api/v1/drivers/me`
- **Access:** `DRIVER`

### 4.3 Update Real-Time GPS Location
- **Route:** `POST /api/v1/drivers/location`
- **Access:** `DRIVER`
- **Request Body:**
```json
{
  "latitude": 12.9720,
  "longitude": 77.5950
}
```

---

## 5. Orders & Packages (`/api/v1/orders`)

### 5.1 Create Order
- **Route:** `POST /api/v1/orders`
- **Access:** Authenticated (`CUSTOMER`, `ADMIN`, `WAREHOUSE_MANAGER`)
- **Request Body:**
```json
{
  "warehouse_id": 1,
  "destination_address": "88, 100 Feet Road, Indiranagar",
  "destination_city": "Bengaluru",
  "destination_state": "Karnataka",
  "destination_postal_code": "560038",
  "destination_latitude": 12.9784,
  "destination_longitude": 77.6408,
  "priority": "HIGH",
  "package": {
    "weight_kg": 12.5,
    "length_cm": 45.0,
    "width_cm": 30.0,
    "height_cm": 25.0,
    "category": "MEDICAL_EQUIPMENT",
    "is_fragile": true,
    "requires_cold_storage": false
  }
}
```

### 5.2 Public Tracking Lookup
- **Route:** `GET /api/v1/orders/track/{tracking_or_order_number}`
- **Access:** Public (No authorization required)
- **Parameters:** Order number (e.g., `ORD-20261015-BLR01`) or Tracking number (e.g., `TRK-IND-9021`)

---

## 6. Deliveries & State Machine (`/api/v1/deliveries`)

### 6.1 Dispatch Order
- **Route:** `POST /api/v1/deliveries/dispatch`
- **Access:** `ADMIN`, `WAREHOUSE_MANAGER`
- **Request Body:**
```json
{
  "order_id": 1,
  "driver_id": 1,
  "vehicle_id": 1,
  "warehouse_id": 1
}
```

### 6.2 Transition Delivery Status
- **Route:** `POST /api/v1/deliveries/{id}/status`
- **Access:** `DRIVER` (assigned) or `WAREHOUSE_MANAGER`, `ADMIN`
- **Allowed Transitions:**
  - `DISPATCHED` &rarr; `IN_TRANSIT`
  - `IN_TRANSIT` &rarr; `OUT_FOR_DELIVERY`
  - `OUT_FOR_DELIVERY` &rarr; `DELIVERED`, `FAILED`, `CANCELLED`
- **Request Body:**
```json
{
  "to_status": "IN_TRANSIT",
  "notes": "Driver departed warehouse bay 4",
  "latitude": 13.0285,
  "longitude": 77.5197
}
```

### 6.3 Proof of Delivery OTP Verification
- **Route:** `POST /api/v1/deliveries/{id}/verify-otp`
- **Access:** `DRIVER`, `ADMIN`
- **Request Body:**
```json
{
  "otp_code": "784912",
  "notes": "Package handed over in person to recipient"
}
```
- **Result:** Validates OTP, marks delivery `DELIVERED`, records actual timestamp, frees driver and vehicle to `AVAILABLE`.
