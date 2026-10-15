import pytest
from datetime import datetime, timezone, timedelta
from backend.app.models.user import User
from backend.app.models.customer import Customer
from backend.app.models.warehouse import Warehouse
from backend.app.models.vehicle import Vehicle
from backend.app.models.driver import Driver
from backend.app.models.order import Order
from backend.app.models.package import Package
from backend.app.models.delivery import Delivery
from backend.app.models.notification import Notification
from backend.app.models.enums import (
    UserRole,
    DriverStatus,
    VehicleStatus,
    VehicleType,
    OrderStatus,
    DeliveryPriority,
    DeliveryFailureReason,
    NotificationType,
    NotificationSeverity,
)


@pytest.fixture
def pod_setup(db_session, auth_tokens):
    """Set up warehouse, vehicle, driver, customer, and order for POD testing."""
    manager_user = auth_tokens["users"]["manager"]
    customer_user = auth_tokens["users"]["customer"]
    driver_user = auth_tokens["users"]["driver"]
    customer = db_session.query(Customer).filter(Customer.user_id == customer_user.id).first()

    warehouse = db_session.query(Warehouse).first()
    if not warehouse:
        warehouse = Warehouse(
            code="WH-POD-01",
            name="POD Test Hub",
            address_line1="123 Hub St",
            city="Bengaluru",
            state="Karnataka",
            postal_code="560001",
            latitude=12.9716,
            longitude=77.5946,
            manager_id=manager_user.id,
        )
        db_session.add(warehouse)
        db_session.flush()

    vehicle = Vehicle(
        registration_number="KA-POD-1001",
        model="POD Electric Van",
        vehicle_type=VehicleType.ELECTRIC_VAN,
        max_weight_capacity_kg=1200.0,
        max_volume_capacity_m3=8.0,
        fuel_type="ELECTRIC",
        fuel_efficiency_kmpl=20.0,
        status=VehicleStatus.AVAILABLE,
    )
    db_session.add(vehicle)
    db_session.flush()

    driver = Driver(
        user_id=driver_user.id,
        license_number="DL-POD-2026-001",
        current_vehicle_id=vehicle.id,
        status=DriverStatus.AVAILABLE,
        rating=4.9,
    )
    db_session.add(driver)
    db_session.flush()

    order = Order(
        order_number="ORD-POD-TEST-001",
        customer_id=customer.id,
        warehouse_id=warehouse.id,
        destination_address="45 Delivery Rd, Indiranagar",
        destination_city="Bengaluru",
        destination_state="Karnataka",
        destination_postal_code="560038",
        destination_latitude=12.9784,
        destination_longitude=77.6408,
        priority=DeliveryPriority.HIGH,
        status=OrderStatus.READY_FOR_DISPATCH,
        estimated_distance_km=12.5,
        estimated_delivery_cost=250.0,
    )
    db_session.add(order)
    db_session.flush()

    package = Package(
        order_id=order.id,
        tracking_number="TRK-POD-001",
        weight_kg=6.5,
        volume_m3=0.02,
        category="ELECTRONICS",
        is_ready_for_dispatch=True,
    )
    db_session.add(package)
    db_session.commit()

    return {
        "manager_user": manager_user,
        "customer_user": customer_user,
        "driver_user": driver_user,
        "customer": customer,
        "warehouse": warehouse,
        "vehicle": vehicle,
        "driver": driver,
        "order": order,
        "package": package,
    }


def test_pod_otp_verification_success_flow(client, auth_tokens, pod_setup):
    """Test full dispatch -> OTP verification success flow with notifications."""
    driver_headers = auth_tokens["driver"]
    manager_headers = auth_tokens["manager"]
    customer_headers = auth_tokens["customer"]

    # 1. Dispatch Order
    dispatch_res = client.post(
        "/api/v1/deliveries/dispatch",
        json={
            "order_id": pod_setup["order"].id,
            "driver_id": pod_setup["driver"].id,
            "vehicle_id": pod_setup["vehicle"].id,
            "warehouse_id": pod_setup["warehouse"].id,
        },
        headers=manager_headers,
    )
    assert dispatch_res.status_code == 201
    del_data = dispatch_res.json()
    del_id = del_data["id"]

    # 2. Check Customer received dispatch notification
    notifs_res = client.get("/api/v1/notifications", headers=customer_headers)
    assert notifs_res.status_code == 200
    customer_notifs = notifs_res.json()
    assert len(customer_notifs) >= 1
    assert any("Dispatched" in n["title"] for n in customer_notifs)

    # 3. Fetch OTP for verification from DB
    from backend.app.models.delivery import Delivery
    from backend.app.core.database import get_db

    db = next(client.app.dependency_overrides[get_db]())
    delivery_obj = db.query(Delivery).filter(Delivery.id == del_id).first()
    correct_otp = delivery_obj.otp_code
    assert len(correct_otp) == 6

    # 4. Complete delivery via OTP verification
    verify_res = client.post(
        f"/api/v1/deliveries/{del_id}/verify-otp",
        json={
            "otp_code": correct_otp,
            "recipient_name": "Rohan Sharma",
            "notes": "Delivered to recipient securely with valid OTP",
            "pod_photo_url": "https://cdn.ildo.com/pod/demo.jpg",
        },
        headers=driver_headers,
    )
    assert verify_res.status_code == 200
    verified_data = verify_res.json()
    assert verified_data["status"] == "DELIVERED"
    assert verified_data["recipient_name"] == "Rohan Sharma"
    assert verified_data["pod_photo_url"] == "https://cdn.ildo.com/pod/demo.jpg"

    # 5. Verify Driver & Vehicle status reset to AVAILABLE
    db.refresh(pod_setup["driver"])
    db.refresh(pod_setup["vehicle"])
    assert pod_setup["driver"].status == DriverStatus.AVAILABLE
    assert pod_setup["vehicle"].status == VehicleStatus.AVAILABLE
    assert pod_setup["driver"].total_deliveries_completed == 1

    # 6. Verify Customer received delivery completion notification
    notifs_res2 = client.get("/api/v1/notifications", headers=customer_headers)
    assert notifs_res2.status_code == 200
    completion_notifs = [n for n in notifs_res2.json() if "Delivered" in n["title"]]
    assert len(completion_notifs) >= 1


def test_pod_otp_invalid_and_attempt_limit_lockout(client, auth_tokens, pod_setup):
    """Test OTP mismatch attempt tracking and 5-attempt lockout security."""
    manager_headers = auth_tokens["manager"]
    driver_headers = auth_tokens["driver"]

    # Dispatch delivery
    dispatch_res = client.post(
        "/api/v1/deliveries/dispatch",
        json={
            "order_id": pod_setup["order"].id,
            "driver_id": pod_setup["driver"].id,
            "vehicle_id": pod_setup["vehicle"].id,
            "warehouse_id": pod_setup["warehouse"].id,
        },
        headers=manager_headers,
    )
    del_id = dispatch_res.json()["id"]

    # Send wrong OTP 4 times
    for attempt in range(1, 5):
        fail_res = client.post(
            f"/api/v1/deliveries/{del_id}/verify-otp",
            json={"otp_code": "000000"},
            headers=driver_headers,
        )
        assert fail_res.status_code == 400
        assert f"{5 - attempt} attempt(s) remaining" in fail_res.json()["detail"]

    # 5th attempt failure
    fail_res5 = client.post(
        f"/api/v1/deliveries/{del_id}/verify-otp",
        json={"otp_code": "000000"},
        headers=driver_headers,
    )
    assert fail_res5.status_code == 400
    assert "0 attempt(s) remaining" in fail_res5.json()["detail"]

    # 6th attempt should be locked out
    lockout_res = client.post(
        f"/api/v1/deliveries/{del_id}/verify-otp",
        json={"otp_code": "000000"},
        headers=driver_headers,
    )
    assert lockout_res.status_code == 400
    assert "Maximum OTP verification attempts (5) exceeded" in lockout_res.json()["detail"]


def test_pod_otp_expiration_and_regeneration(client, auth_tokens, pod_setup):
    """Test expired OTP rejection and regeneration workflow."""
    manager_headers = auth_tokens["manager"]
    customer_headers = auth_tokens["customer"]
    driver_headers = auth_tokens["driver"]

    # Dispatch delivery
    dispatch_res = client.post(
        "/api/v1/deliveries/dispatch",
        json={
            "order_id": pod_setup["order"].id,
            "driver_id": pod_setup["driver"].id,
            "vehicle_id": pod_setup["vehicle"].id,
            "warehouse_id": pod_setup["warehouse"].id,
        },
        headers=manager_headers,
    )
    del_id = dispatch_res.json()["id"]

    from backend.app.core.database import get_db
    from backend.app.models.delivery import Delivery

    db = next(client.app.dependency_overrides[get_db]())
    delivery_obj = db.query(Delivery).filter(Delivery.id == del_id).first()

    # Artificially set expiry in the past
    delivery_obj.otp_expires_at = datetime.now(timezone.utc) - timedelta(minutes=10)
    db.commit()

    # Attempt verification with expired OTP -> Should fail with 400
    expired_res = client.post(
        f"/api/v1/deliveries/{del_id}/verify-otp",
        json={"otp_code": delivery_obj.otp_code},
        headers=driver_headers,
    )
    assert expired_res.status_code == 400
    assert "Delivery OTP has expired" in expired_res.json()["detail"]

    # Customer regenerates OTP
    regen_res = client.post(
        f"/api/v1/deliveries/{del_id}/regenerate-otp",
        headers=customer_headers,
    )
    assert regen_res.status_code == 200
    regen_data = regen_res.json()
    new_otp = regen_data["otp_code"]
    assert len(new_otp) == 6

    # Verify new OTP succeeds
    verify_res = client.post(
        f"/api/v1/deliveries/{del_id}/verify-otp",
        json={"otp_code": new_otp, "recipient_name": "Verified Customer"},
        headers=driver_headers,
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["status"] == "DELIVERED"


def test_delivery_failure_reporting(client, auth_tokens, pod_setup):
    """Test driver reporting delivery failure with reason codes."""
    manager_headers = auth_tokens["manager"]
    driver_headers = auth_tokens["driver"]
    customer_headers = auth_tokens["customer"]

    # Dispatch delivery
    dispatch_res = client.post(
        "/api/v1/deliveries/dispatch",
        json={
            "order_id": pod_setup["order"].id,
            "driver_id": pod_setup["driver"].id,
            "vehicle_id": pod_setup["vehicle"].id,
            "warehouse_id": pod_setup["warehouse"].id,
        },
        headers=manager_headers,
    )
    del_id = dispatch_res.json()["id"]

    # Driver reports failure
    fail_res = client.post(
        f"/api/v1/deliveries/{del_id}/report-failure",
        json={
            "reason": "RECIPIENT_UNAVAILABLE",
            "notes": "Door locked, recipient not answering phone calls at indiranagar",
            "latitude": 12.9784,
            "longitude": 77.6408,
            "photo_url": "https://cdn.ildo.com/proof/locked_gate.jpg",
        },
        headers=driver_headers,
    )
    assert fail_res.status_code == 200
    del_data = fail_res.json()
    assert del_data["status"] == "FAILED"
    assert "RECIPIENT_UNAVAILABLE" in del_data["failure_reason"]
    assert del_data["pod_photo_url"] == "https://cdn.ildo.com/proof/locked_gate.jpg"

    # Verify Customer received failure alert
    notifs_res = client.get("/api/v1/notifications", headers=customer_headers)
    assert notifs_res.status_code == 200
    fail_notifs = [n for n in notifs_res.json() if "Failed" in n["title"]]
    assert len(fail_notifs) >= 1
    assert fail_notifs[0]["severity"] == "CRITICAL"


def test_notifications_api_lifecycle(client, auth_tokens, pod_setup):
    """Test fetching notifications, checking unread count, and marking read."""
    customer_headers = auth_tokens["customer"]

    # 1. Unread count
    count_res = client.get("/api/v1/notifications/unread-count", headers=customer_headers)
    assert count_res.status_code == 200

    # 2. List notifications
    list_res = client.get("/api/v1/notifications", headers=customer_headers)
    assert list_res.status_code == 200
    notifs = list_res.json()

    if len(notifs) > 0:
        first_id = notifs[0]["id"]
        # Mark single as read
        read_res = client.put(f"/api/v1/notifications/{first_id}/read", headers=customer_headers)
        assert read_res.status_code == 200
        assert read_res.json()["is_read"] is True

    # 3. Mark all as read
    all_read_res = client.put("/api/v1/notifications/read-all", headers=customer_headers)
    assert all_read_res.status_code == 200

    # 4. Verify unread count is now 0
    final_count = client.get("/api/v1/notifications/unread-count", headers=customer_headers)
    assert final_count.status_code == 200
    assert final_count.json()["unread_count"] == 0
