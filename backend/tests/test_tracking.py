import pytest
from datetime import datetime, timedelta, timezone
from backend.app.models.user import User
from backend.app.models.warehouse import Warehouse
from backend.app.models.vehicle import Vehicle
from backend.app.models.driver import Driver
from backend.app.models.order import Order
from backend.app.models.package import Package
from backend.app.models.delivery import Delivery
from backend.app.models.enums import (
    UserRole,
    DriverStatus,
    VehicleStatus,
    VehicleType,
    OrderStatus,
    DeliveryPriority,
    DelayRiskCategory,
)
from backend.app.core.security import get_password_hash, create_access_token
from backend.app.intelligence.eta import DynamicETACalculator
from backend.app.intelligence.delay import DelayRiskDetector


@pytest.fixture
def tracking_test_data(db_session):
    """Sets up an active delivery scenario with driver, vehicle, and promised delivery time."""
    driver_user = User(
        email="tracking_driver@ildo.com",
        hashed_password=get_password_hash("DriverPass123!"),
        full_name="Live Tracking Driver",
        role=UserRole.DRIVER,
        is_active=True,
    )
    db_session.add(driver_user)
    db_session.flush()

    wh = Warehouse(
        name="Peenya Central Depot",
        code="WH-TRK-01",
        address_line1="Peenya Industrial Area",
        city="Bengaluru",
        state="Karnataka",
        postal_code="560058",
        latitude=13.0285,
        longitude=77.5197,
    )
    db_session.add(wh)
    db_session.flush()

    veh = Vehicle(
        registration_number="KA-01-TRK-99",
        model="Tata Ace EV",
        vehicle_type=VehicleType.ELECTRIC_VAN,
        max_weight_capacity_kg=1000.0,
        max_volume_capacity_m3=6.0,
        status=VehicleStatus.IN_SERVICE,
    )
    db_session.add(veh)
    db_session.flush()

    drv = Driver(
        user_id=driver_user.id,
        license_number="DL-TRK-001",
        current_vehicle_id=veh.id,
        status=DriverStatus.BUSY,
        current_latitude=13.0100,
        current_longitude=77.5300,
        last_location_updated_at=datetime.now(timezone.utc),
        rating=4.9,
    )
    db_session.add(drv)
    db_session.flush()

    # Order promised delivery in 45 minutes
    promised_time = datetime.now(timezone.utc) + timedelta(minutes=45)
    order = Order(
        order_number="ORD-LIVE-TRK-01",
        customer_id=1,
        warehouse_id=wh.id,
        destination_address="Koramangala 5th Block",
        destination_city="Bengaluru",
        destination_state="Karnataka",
        destination_postal_code="560095",
        destination_latitude=12.9352,
        destination_longitude=77.6245,
        status=OrderStatus.IN_TRANSIT,
        promised_delivery_time=promised_time,
    )
    db_session.add(order)
    db_session.flush()

    pkg = Package(
        order_id=order.id,
        tracking_number="TRK-LIVE-99",
        weight_kg=8.5,
    )
    db_session.add(pkg)
    db_session.flush()

    delivery = Delivery(
        delivery_number="DEL-LIVE-TRK-01",
        order_id=order.id,
        driver_id=drv.id,
        vehicle_id=veh.id,
        warehouse_id=wh.id,
        status=OrderStatus.IN_TRANSIT,
        otp_code="554433",
    )
    db_session.add(delivery)
    db_session.commit()

    return {
        "driver_token": {"Authorization": f"Bearer {create_access_token(driver_user.id, driver_user.role.value)}"},
        "delivery_id": delivery.id,
        "driver": drv,
        "order": order,
        "promised_time": promised_time,
    }


def test_dynamic_eta_calculator_unit():
    """Unit test verifying dynamic ETA, road circuity, traffic multipliers, and confidence bounds."""
    # Distance from Peenya (13.0285, 77.5197) to Koramangala (12.9352, 77.6245) is ~15 km straight line
    now = datetime.now(timezone.utc)
    res = DynamicETACalculator.calculate_eta(
        current_lat=13.0285,
        current_lon=77.5197,
        dest_lat=12.9352,
        dest_lon=77.6245,
        current_speed_kmph=30.0,
        departure_time=now,
    )
    assert res["straight_line_distance_km"] > 10.0
    assert res["remaining_distance_km"] >= res["straight_line_distance_km"]
    assert res["estimated_duration_minutes"] > 15.0
    assert res["estimated_arrival_time"] > now
    assert res["uncertainty_buffer_minutes"] > 3.0
    assert res["confidence_lower_bound"] < res["estimated_arrival_time"] < res["confidence_upper_bound"]


def test_delay_risk_detector_unit():
    """Unit test assessing delay risk classifications."""
    now = datetime.now(timezone.utc)

    # 1. On Track: arrival 30 mins before promised time -> NONE
    promised_future = now + timedelta(minutes=60)
    arrival_early = now + timedelta(minutes=30)
    risk_none = DelayRiskDetector.evaluate_delay_risk(arrival_early, promised_future)
    assert risk_none["risk_level"] == DelayRiskCategory.NONE.value
    assert risk_none["is_delayed"] is False

    # 2. Moderate Delay: arrival 8 mins after promised -> MEDIUM
    promised_tight = now + timedelta(minutes=30)
    arrival_moderate_delay = now + timedelta(minutes=38)
    risk_med = DelayRiskDetector.evaluate_delay_risk(arrival_moderate_delay, promised_tight)
    assert risk_med["risk_level"] == DelayRiskCategory.MEDIUM.value
    assert risk_med["is_delayed"] is True

    # 3. Critical Delay: arrival 25 mins after promised -> HIGH
    arrival_critical = now + timedelta(minutes=55)
    risk_high = DelayRiskDetector.evaluate_delay_risk(arrival_critical, promised_tight)
    assert risk_high["risk_level"] == DelayRiskCategory.HIGH.value
    assert risk_high["is_delayed"] is True


def test_live_tracking_rest_snapshot_endpoint(client, tracking_test_data):
    """Integration test verifying GET /api/v1/tracking/{id}/live snapshot endpoint."""
    del_id = tracking_test_data["delivery_id"]
    res = client.get(f"/api/v1/tracking/{del_id}/live")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["delivery_id"] == del_id
    assert data["status"] == "IN_TRANSIT"
    assert data["driver_name"] == "Live Tracking Driver"
    assert data["origin_warehouse"]["name"] == "Peenya Central Depot"
    assert data["remaining_distance_km"] > 0.0
    assert data["delay_risk_level"] in ["NONE", "LOW", "MEDIUM", "HIGH"]
    assert data["connection_mode"] == "REST_SNAPSHOT"


def test_driver_gps_ping_endpoint(client, tracking_test_data):
    """Test driver submitting live GPS coordinates via REST."""
    del_id = tracking_test_data["delivery_id"]
    headers = tracking_test_data["driver_token"]

    ping_payload = {
        "latitude": 12.9800,
        "longitude": 77.5600,
        "speed_kmph": 32.5,
        "accuracy_meters": 4.5,
        "heading_degrees": 135.0,
    }
    res = client.post(f"/api/v1/tracking/{del_id}/ping", json=ping_payload, headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "success"
    assert data["latitude"] == 12.9800
    assert data["longitude"] == 77.5600
    assert data["remaining_distance_km"] > 0


def test_websocket_tracking_stream_handshake(client, tracking_test_data):
    """Test client establishing WebSocket connection to live delivery tracking stream."""
    del_id = tracking_test_data["delivery_id"]

    with client.websocket_connect(f"/api/v1/tracking/ws/{del_id}") as ws:
        # Initial message received immediately upon connecting
        msg = ws.receive_json()
        assert msg["delivery_id"] == del_id
        assert msg["driver_name"] == "Live Tracking Driver"
        assert msg["connection_mode"] == "WEBSOCKET_LIVE"

        # Send heartbeat ping
        ws.send_json({"action": "ping"})
        pong = ws.receive_json()
        assert pong["action"] == "pong"
