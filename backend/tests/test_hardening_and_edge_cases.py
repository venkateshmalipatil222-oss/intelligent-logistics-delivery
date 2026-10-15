import pytest
from datetime import datetime, timezone, timedelta
from backend.app.models.warehouse import Warehouse
from backend.app.models.vehicle import Vehicle
from backend.app.models.driver import Driver
from backend.app.models.order import Order
from backend.app.models.package import Package
from backend.app.models.delivery import Delivery
from backend.app.models.user import User
from backend.app.models.enums import (
    VehicleType,
    VehicleStatus,
    DriverStatus,
    OrderStatus,
    DeliveryPriority,
    UserRole,
)
from backend.app.intelligence.eta import DynamicETACalculator
from backend.app.intelligence.delay import DelayRiskDetector


@pytest.fixture
def hardening_seed(db_session, auth_tokens):
    """Seed baseline operational infrastructure for hardening tests."""
    now = datetime.now(timezone.utc)

    # 1. Warehouse
    wh = Warehouse(
        name="Hardening Central Hub",
        code="WH-HARD-01",
        address_line1="Outer Ring Road",
        city="Bengaluru",
        state="Karnataka",
        postal_code="560103",
        latitude=12.9279,
        longitude=77.6841,
        capacity_sqft=15000.0,
        is_active=True,
    )
    db_session.add(wh)
    db_session.flush()

    # 2. Vehicles: Standard van, small bike, maintenance truck
    v_van = Vehicle(
        registration_number="KA-01-HD-0001",
        model="Force Delivery Van",
        vehicle_type=VehicleType.VAN,
        max_weight_capacity_kg=1200.0,
        max_volume_capacity_m3=7.0,
        fuel_type="DIESEL",
        fuel_efficiency_kmpl=11.5,
        status=VehicleStatus.AVAILABLE,
    )
    v_bike = Vehicle(
        registration_number="KA-01-HD-0002",
        model="Hero Electric Bike",
        vehicle_type=VehicleType.BIKE,
        max_weight_capacity_kg=25.0,
        max_volume_capacity_m3=0.08,
        fuel_type="ELECTRIC",
        fuel_efficiency_kmpl=45.0,
        status=VehicleStatus.AVAILABLE,
    )
    v_maint = Vehicle(
        registration_number="KA-01-HD-0003",
        model="Tata 407",
        vehicle_type=VehicleType.TRUCK,
        max_weight_capacity_kg=3500.0,
        max_volume_capacity_m3=14.0,
        fuel_type="DIESEL",
        fuel_efficiency_kmpl=7.0,
        status=VehicleStatus.MAINTENANCE,
    )
    db_session.add_all([v_van, v_bike, v_maint])
    db_session.flush()

    # 3. Drivers: Driver 1 (assigned to auth_tokens driver), Driver 2 (offline), Driver 3 (second driver)
    driver1 = Driver(
        user_id=auth_tokens["users"]["driver"].id,
        license_number="DL-HARD-001",
        current_vehicle_id=v_van.id,
        status=DriverStatus.AVAILABLE,
        current_latitude=12.9280,
        current_longitude=77.6840,
        total_deliveries_completed=5,
        rating=4.8,
    )

    driver_offline = Driver(
        user_id=auth_tokens["users"]["manager"].id,  # reuse user for offline driver dummy
        license_number="DL-HARD-OFFLINE",
        current_vehicle_id=None,
        status=DriverStatus.OFFLINE,
        total_deliveries_completed=0,
    )
    db_session.add_all([driver1, driver_offline])
    db_session.flush()

    # 4. Standard Order
    cust_id = auth_tokens["customer_id"]
    order = Order(
        order_number="ORD-HARD-001",
        customer_id=cust_id,
        warehouse_id=wh.id,
        destination_address="Bellandur EcoSpace",
        destination_city="Bengaluru",
        destination_state="Karnataka",
        destination_postal_code="560103",
        destination_latitude=12.9260,
        destination_longitude=77.6762,
        priority=DeliveryPriority.MEDIUM,
        status=OrderStatus.CREATED,
        estimated_distance_km=4.5,
        estimated_delivery_cost=95.0,
    )
    db_session.add(order)
    db_session.flush()

    pkg = Package(
        order_id=order.id,
        tracking_number="TRK-HARD-001",
        weight_kg=15.0,
        volume_m3=0.03,
        is_ready_for_dispatch=True,
    )
    db_session.add(pkg)

    # 5. Heavy Overweight Order (exceeds bike payload limit)
    order_heavy = Order(
        order_number="ORD-HARD-HEAVY",
        customer_id=cust_id,
        warehouse_id=wh.id,
        destination_address="Whitefield Tech Park",
        destination_city="Bengaluru",
        destination_state="Karnataka",
        destination_postal_code="560066",
        destination_latitude=12.9856,
        destination_longitude=77.7374,
        priority=DeliveryPriority.HIGH,
        status=OrderStatus.CREATED,
    )
    db_session.add(order_heavy)
    db_session.flush()

    pkg_heavy = Package(
        order_id=order_heavy.id,
        tracking_number="TRK-HARD-HEAVY",
        weight_kg=50.0,  # 50kg exceeds bike's 25kg max
        volume_m3=0.2,
        is_ready_for_dispatch=True,
    )
    db_session.add(pkg_heavy)
    db_session.commit()

    return {
        "wh": wh,
        "v_van": v_van,
        "v_bike": v_bike,
        "v_maint": v_maint,
        "driver1": driver1,
        "driver_offline": driver_offline,
        "order": order,
        "order_heavy": order_heavy,
    }


# =============================================================================
# 1. State Machine & Transition Hardening
# =============================================================================

def test_illegal_transition_from_terminal_delivered_state(client, auth_tokens, hardening_seed, db_session):
    """Ensure once an order is DELIVERED, it cannot transition back to IN_TRANSIT or DISPATCHED."""
    # First, dispatch order
    dispatch_payload = {
        "order_id": hardening_seed["order"].id,
        "driver_id": hardening_seed["driver1"].id,
        "vehicle_id": hardening_seed["v_van"].id,
        "warehouse_id": hardening_seed["wh"].id,
    }
    disp_res = client.post("/api/v1/deliveries/dispatch", json=dispatch_payload, headers=auth_tokens["manager"])
    assert disp_res.status_code == 201
    del_id = disp_res.json()["id"]

    # Transition: DISPATCHED -> IN_TRANSIT -> OUT_FOR_DELIVERY
    client.post(f"/api/v1/deliveries/{del_id}/status", json={"to_status": "IN_TRANSIT"}, headers=auth_tokens["admin"])
    client.post(f"/api/v1/deliveries/{del_id}/status", json={"to_status": "OUT_FOR_DELIVERY"}, headers=auth_tokens["admin"])

    # Complete handover with valid OTP
    del_record = db_session.query(Delivery).filter(Delivery.id == del_id).first()
    otp = del_record.otp_code
    verify_res = client.post(
        f"/api/v1/deliveries/{del_id}/verify-otp",
        json={"otp_code": otp, "recipient_name": "Test Handover"},
        headers=auth_tokens["admin"],
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["status"] == "DELIVERED"

    # ILLEGAL: Try to move terminal DELIVERED delivery back to DISPATCHED
    illegal_res = client.post(
        f"/api/v1/deliveries/{del_id}/status",
        json={"to_status": "DISPATCHED"},
        headers=auth_tokens["admin"],
    )
    assert illegal_res.status_code == 400
    assert "Invalid state transition" in illegal_res.json()["detail"]

    # ILLEGAL: Try to verify OTP on already DELIVERED delivery
    duplicate_otp_res = client.post(
        f"/api/v1/deliveries/{del_id}/verify-otp",
        json={"otp_code": otp},
        headers=auth_tokens["admin"],
    )
    assert duplicate_otp_res.status_code == 400
    assert "already been completed" in duplicate_otp_res.json()["detail"]


def test_cannot_dispatch_already_dispatched_order(client, auth_tokens, hardening_seed):
    """Ensure duplicate dispatch requests on an active order are strictly rejected."""
    dispatch_payload = {
        "order_id": hardening_seed["order"].id,
        "driver_id": hardening_seed["driver1"].id,
        "vehicle_id": hardening_seed["v_van"].id,
        "warehouse_id": hardening_seed["wh"].id,
    }
    res1 = client.post("/api/v1/deliveries/dispatch", json=dispatch_payload, headers=auth_tokens["manager"])
    assert res1.status_code == 201

    # Attempt second dispatch on same order
    res2 = client.post("/api/v1/deliveries/dispatch", json=dispatch_payload, headers=auth_tokens["manager"])
    assert res2.status_code == 400
    assert "already in state" in res2.json()["detail"]


# =============================================================================
# 2. Constraint & Overload Enforcement Hardening
# =============================================================================

def test_dispatch_fails_with_offline_driver(client, auth_tokens, hardening_seed):
    """Ensure system rejects dispatching deliveries to an OFFLINE driver."""
    payload = {
        "order_id": hardening_seed["order"].id,
        "driver_id": hardening_seed["driver_offline"].id,
        "vehicle_id": hardening_seed["v_van"].id,
        "warehouse_id": hardening_seed["wh"].id,
    }
    response = client.post("/api/v1/deliveries/dispatch", json=payload, headers=auth_tokens["manager"])
    assert response.status_code == 400
    assert "OFFLINE" in response.json()["detail"]


def test_dispatch_fails_with_maintenance_vehicle(client, auth_tokens, hardening_seed):
    """Ensure system rejects dispatching using a vehicle currently under MAINTENANCE."""
    payload = {
        "order_id": hardening_seed["order"].id,
        "driver_id": hardening_seed["driver1"].id,
        "vehicle_id": hardening_seed["v_maint"].id,
        "warehouse_id": hardening_seed["wh"].id,
    }
    response = client.post("/api/v1/deliveries/dispatch", json=payload, headers=auth_tokens["manager"])
    assert response.status_code == 400
    assert "MAINTENANCE" in response.json()["detail"]


def test_dispatch_fails_when_package_weight_exceeds_vehicle_capacity(client, auth_tokens, hardening_seed):
    """Ensure system enforces physical payload capacity limits (50kg package on 25kg bike)."""
    payload = {
        "order_id": hardening_seed["order_heavy"].id,
        "driver_id": hardening_seed["driver1"].id,
        "vehicle_id": hardening_seed["v_bike"].id,  # 25kg max capacity
        "warehouse_id": hardening_seed["wh"].id,
    }
    response = client.post("/api/v1/deliveries/dispatch", json=payload, headers=auth_tokens["manager"])
    assert response.status_code == 400
    assert "exceeds vehicle" in response.json()["detail"]


# =============================================================================
# 3. Security, RBAC & Parameter Sanitization Hardening
# =============================================================================

def test_tampered_jwt_token_rejection(client):
    """Ensure malformed, tampered, or fabricated JWT tokens are immediately blocked."""
    tampered_headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.payload"}
    response = client.get("/api/v1/users/me", headers=tampered_headers)
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]


def test_customer_cannot_access_unowned_order(client, auth_tokens, db_session):
    """Ensure multi-tenant isolation prevents customers from viewing other accounts' orders."""
    # Create another customer and order
    other_user = User(
        email="stranger@corp.com",
        hashed_password="SecretPassword123!",
        full_name="Stranger User",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db_session.add(other_user)
    db_session.flush()

    other_order = Order(
        order_number="ORD-STRANGER-999",
        customer_id=9999,  # different customer
        destination_address="Confidential Location",
        destination_city="Mumbai",
        destination_state="Maharashtra",
        destination_postal_code="400001",
        destination_latitude=19.0760,
        destination_longitude=72.8777,
    )
    db_session.add(other_order)
    db_session.commit()

    # Logged-in test customer attempts to inspect stranger's order
    response = client.get(f"/api/v1/orders/{other_order.id}", headers=auth_tokens["customer"])
    assert response.status_code == 403
    assert "You do not own this order" in response.json()["detail"]


# =============================================================================
# 4. Algorithmic Edge Cases & Numerical Robustness
# =============================================================================

def test_dijkstra_coincident_origin_destination_bounds(client, auth_tokens):
    """Verify Dijkstra pathfinding handles identical origin and destination without crashes."""
    payload = {
        "origin_latitude": 12.9716,
        "origin_longitude": 77.5946,
        "destination_latitude": 12.9716,
        "destination_longitude": 77.5946,
        "origin_name": "MG Road Depot",
        "destination_name": "MG Road Dropoff",
    }
    response = client.post("/api/v1/intelligence/optimize-route", json=payload, headers=auth_tokens["admin"])
    assert response.status_code == 200
    data = response.json()
    assert data["straight_line_distance_km"] == 0.0
    assert data["network_distance_km"] >= 0.0
    assert data["estimated_duration_minutes"] > 0


def test_tsp_stops_length_validation(client, auth_tokens):
    """Ensure TSP multi-stop sequencing enforces minimum requirement of >= 2 stops."""
    payload = {
        "depot_latitude": 12.9716,
        "depot_longitude": 77.5946,
        "stops": [
            {"id": "STOP-1", "label": "Single Stop Only", "latitude": 12.9750, "longitude": 77.6000}
        ],
    }
    response = client.post("/api/v1/intelligence/optimize-multi-stop", json=payload, headers=auth_tokens["admin"])
    assert response.status_code == 422  # Pydantic min_length=2 rejection


def test_dynamic_eta_zero_speed_and_speeding_bounds():
    """Verify DynamicETACalculator handles stationary (0 km/h) and high speed extremes safely."""
    now = datetime.now(timezone.utc)

    # Stationary (speed = 0)
    eta_zero = DynamicETACalculator.calculate_eta(
        current_lat=12.9716,
        current_lon=77.5946,
        dest_lat=12.9800,
        dest_lon=77.6100,
        current_speed_kmph=0.0,
        departure_time=now,
    )
    assert eta_zero["effective_speed_kmph"] == DynamicETACalculator.BASELINE_SPEED_KMPH
    assert eta_zero["estimated_duration_minutes"] > 5.0
    assert eta_zero["estimated_arrival_time"] > now

    # High speed (speed = 120 km/h) capped by urban max clamp (55.0)
    eta_fast = DynamicETACalculator.calculate_eta(
        current_lat=12.9716,
        current_lon=77.5946,
        dest_lat=12.9800,
        dest_lon=77.6100,
        current_speed_kmph=120.0,
        departure_time=now,
    )
    assert eta_fast["effective_speed_kmph"] <= 55.0


def test_delay_risk_detector_naive_and_aware_datetimes():
    """Verify DelayRiskDetector correctly compares naive and aware datetimes without TypeErrors."""
    now_aware = datetime.now(timezone.utc)
    arrival_naive = datetime(2026, 10, 15, 14, 30)  # naive
    promised_aware = datetime(2026, 10, 15, 14, 0, tzinfo=timezone.utc)  # aware (30 mins past SLA)

    risk_result = DelayRiskDetector.evaluate_delay_risk(
        estimated_arrival_time=arrival_naive,
        promised_delivery_time=promised_aware,
        last_ping_time=now_aware - timedelta(minutes=5),
        delivery_status=OrderStatus.IN_TRANSIT,
    )
    assert risk_result["risk_level"] == "HIGH"
    assert risk_result["is_delayed"] is True
    assert risk_result["variance_minutes"] == 30.0
