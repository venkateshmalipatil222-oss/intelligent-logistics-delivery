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

---

## 7. Intelligent Decision & Optimization Engines (`/api/v1/intelligence`)

### 7.1 Recommend Drivers for Order
- **Route:** `GET /api/v1/intelligence/recommend-driver/{order_id}`
- **Access:** `ADMIN`, `WAREHOUSE_MANAGER`
- **Output:** Ranked driver evaluations, multi-factor scores ($S = \sum w_i f_i$), rejection reasons, and human-readable rationale explanations.

### 7.2 AI Auto-Assign & Dispatch
- **Route:** `POST /api/v1/intelligence/auto-assign/{order_id}`
- **Access:** `ADMIN`, `WAREHOUSE_MANAGER`
- **Output:** Evaluates candidates and automatically dispatches to #1 eligible driver, generating OTP and initializing status tracking.

### 7.3 Dijkstra Shortest-Path Route Optimization
- **Route:** `POST /api/v1/intelligence/optimize-route`
- **Access:** Authenticated
- **Request Body:**
```json
{
  "origin_latitude": 12.9716,
  "origin_longitude": 77.5946,
  "destination_latitude": 12.9352,
  "destination_longitude": 77.6245,
  "origin_name": "Bengaluru Central Depot",
  "destination_name": "Koramangala Hub"
}
```
- **Output:** Modeled road distance, circuity factor, waypoints, turn-by-turn legs, and duration.

### 7.4 Multi-Stop Batch Route Optimization (Nearest-Neighbor TSP)
- **Route:** `POST /api/v1/intelligence/optimize-multi-stop`
- **Access:** Authenticated
- **Output:** Sequenced drop-offs with priority bias and distance savings vs unoptimized route.

### 7.5 Transparent Operating Cost Estimation
- **Route:** `POST /api/v1/intelligence/estimate-cost`
- **Access:** Authenticated
- **Output:** Line-item itemization: fuel consumption, driver labor hours, vehicle depreciation, priority surcharge, cold chain preservation, and 18% GST.

---

## 8. Real-Time Geolocation, Dynamic ETA & WebSockets (`/api/v1/tracking`)

### 8.1 Live Tracking REST Snapshot & Fallback
- **Route:** `GET /api/v1/tracking/{delivery_id}/live`
- **Access:** Public / Authenticated (Supports instant initial render and automatic fallback polling)
- **Response (200 OK):**
```json
{
  "delivery_id": 1,
  "delivery_number": "DEL-20261015-99881",
  "status": "DISPATCHED",
  "order_number": "ORD-20261015-BLR01",
  "driver_name": "Suresh Raina",
  "driver_phone": "+919876500003",
  "vehicle_registration": "KA-01-EV-2024",
  "origin_warehouse": {
    "name": "Bengaluru Central Logistics Hub",
    "latitude": 13.0285,
    "longitude": 77.5197
  },
  "destination": {
    "name": "Customer Drop-off Location",
    "latitude": 12.9784,
    "longitude": 77.6408
  },
  "current_driver_location": {
    "latitude": 13.0285,
    "longitude": 77.5197
  },
  "remaining_distance_km": 16.4,
  "estimated_arrival_time": "2026-10-15T12:45:00Z",
  "estimated_duration_minutes": 38.5,
  "uncertainty_buffer_minutes": 7.9,
  "traffic_multiplier": 1.25,
  "delay_risk_level": "LOW",
  "delay_reasons": [],
  "is_telemetry_stale": false,
  "last_ping_seconds_ago": 12.0
}
```

### 8.2 Driver High-Frequency GPS Telemetry Ping
- **Route:** `POST /api/v1/tracking/{delivery_id}/ping`
- **Access:** `DRIVER` (assigned) or `ADMIN`
- **Request Body:**
```json
{
  "latitude": 13.0124,
  "longitude": 77.5489,
  "speed_kmph": 38.5,
  "accuracy_meters": 6.2,
  "heading_degrees": 142.0
}
```
- **Action:** Updates driver location in DB, recalculates dynamic ETA, evaluates delay risk, and broadcasts updated state to all connected customers and warehouse dispatch monitors via WebSocket.

### 8.3 Live Delivery WebSocket Stream (Customer & Admin Monitoring)
- **Route:** `ws://127.0.0.1:8000/api/v1/tracking/ws/{delivery_id}`
- **Protocol:** WebSocket (JSON frames)
- **Features:**
  - Instant live snapshot transmitted upon connection handshake.
  - Real-time broadcasts pushed immediately upon driver GPS ping.
  - Built-in ping/pong keepalive frame handling (`{"action": "ping"}` &rarr; `{"action": "pong"}`).
  - Seamless automatic fallback to 4-second REST polling if network interruptions occur.

### 8.4 Driver Telemetry Broadcast WebSocket Channel
- **Route:** `ws://127.0.0.1:8000/api/v1/tracking/ws/driver/broadcast`
- **Protocol:** WebSocket (JSON frames)
- **Access:** `DRIVER`
- **Payload:** Continuously streams W3C browser geolocation telemetry coordinates to the backend room manager.

