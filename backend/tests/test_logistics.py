import pytest
from backend.app.models.user import User
from backend.app.models.customer import Customer
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
)
from backend.app.core.security import get_password_hash, create_access_token


@pytest.fixture
def auth_tokens(db_session):
    """Creates test users across all roles and returns authentication headers."""
    # 1. Admin
    admin = User(
        email="test_admin@ildo.com",
        hashed_password=get_password_hash("AdminPass123!"),
        full_name="Test Admin",
        role=UserRole.ADMIN,
        is_active=True,
    )
    # 2. Manager
    manager = User(
        email="test_manager@ildo.com",
        hashed_password=get_password_hash("ManagerPass123!"),
        full_name="Test Manager",
        role=UserRole.WAREHOUSE_MANAGER,
        is_active=True,
    )
    # 3. Driver
    driver_user = User(
        email="test_driver@ildo.com",
        hashed_password=get_password_hash("DriverPass123!"),
        full_name="Test Driver",
        role=UserRole.DRIVER,
        is_active=True,
    )
    # 4. Customer
    customer_user = User(
        email="test_customer@ildo.com",
        hashed_password=get_password_hash("CustomerPass123!"),
        full_name="Test Customer",
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db_session.add_all([admin, manager, driver_user, customer_user])
    db_session.flush()

    cust = Customer(
        user_id=customer_user.id,
        company_name="Test Customer Corp",
        city="Bengaluru",
        default_latitude=12.9260,
        default_longitude=77.6762,
    )
    db_session.add(cust)
    db_session.commit()

    return {
        "admin": {"Authorization": f"Bearer {create_access_token(admin.id, admin.role.value)}"},
        "manager": {"Authorization": f"Bearer {create_access_token(manager.id, manager.role.value)}"},
        "driver": {"Authorization": f"Bearer {create_access_token(driver_user.id, driver_user.role.value)}"},
        "customer": {"Authorization": f"Bearer {create_access_token(customer_user.id, customer_user.role.value)}"},
        "users": {
            "admin": admin,
            "manager": manager,
            "driver": driver_user,
            "customer": customer_user,
        },
        "customer_id": cust.id,
    }


def test_warehouse_lifecycle(client, auth_tokens):
    """Test warehouse creation, listing, filtering, and update."""
    headers = auth_tokens["admin"]

    # 1. Create Warehouse
    wh_payload = {
        "name": "Koramangala Staging Hub",
        "code": "WH-KOR-01",
        "address_line1": "80 Feet Road",
        "city": "Bengaluru",
        "state": "Karnataka",
        "postal_code": "560034",
        "latitude": 12.9352,
        "longitude": 77.6245,
        "capacity_sqft": 15000.0,
        "contact_phone": "+918012345678",
        "is_active": True,
    }
    res = client.post("/api/v1/warehouses", json=wh_payload, headers=headers)
    assert res.status_code == 201, res.text
    wh_id = res.json()["id"]
    assert res.json()["code"] == "WH-KOR-01"

    # 2. Duplicate Code Rejection
    res_dup = client.post("/api/v1/warehouses", json=wh_payload, headers=headers)
    assert res_dup.status_code == 409

    # 3. List Warehouses with City Filter
    res_list = client.get("/api/v1/warehouses?city=Bengaluru", headers=headers)
    assert res_list.status_code == 200
    assert any(w["id"] == wh_id for w in res_list.json())

    # 4. Update Warehouse
    res_upd = client.put(f"/api/v1/warehouses/{wh_id}", json={"capacity_sqft": 18000.0}, headers=headers)
    assert res_upd.status_code == 200
    assert res_upd.json()["capacity_sqft"] == 18000.0


def test_vehicle_and_driver_registration(client, auth_tokens):
    """Test vehicle registration, driver registration, and linking."""
    mgr_headers = auth_tokens["manager"]
    driver_headers = auth_tokens["driver"]
    driver_user = auth_tokens["users"]["driver"]

    # 1. Register Vehicle
    veh_payload = {
        "registration_number": "KA-04-EV-9900",
        "model": "Tata Ace EV",
        "vehicle_type": "ELECTRIC_VAN",
        "max_weight_capacity_kg": 1000.0,
        "max_volume_capacity_m3": 5.5,
        "fuel_type": "ELECTRIC",
        "fuel_efficiency_kmpl": 15.0,
        "status": "AVAILABLE",
    }
    res_veh = client.post("/api/v1/vehicles", json=veh_payload, headers=mgr_headers)
    assert res_veh.status_code == 201
    veh_id = res_veh.json()["id"]

    # 2. Register Driver
    drv_payload = {
        "user_id": driver_user.id,
        "license_number": "DL-KA-2022-771122",
        "current_vehicle_id": veh_id,
        "status": "AVAILABLE",
    }
    res_drv = client.post("/api/v1/drivers", json=drv_payload, headers=mgr_headers)
    assert res_drv.status_code == 201
    drv_id = res_drv.json()["id"]
    assert res_drv.json()["vehicle_registration"] == "KA-04-EV-9900"

    # 3. Driver Location Update
    loc_payload = {"latitude": 12.9300, "longitude": 77.6200}
    res_loc = client.post("/api/v1/drivers/location", json=loc_payload, headers=driver_headers)
    assert res_loc.status_code == 200
    assert res_loc.json()["status"] == "success"

    # 4. Driver Profile Check
    res_me = client.get("/api/v1/drivers/me", headers=driver_headers)
    assert res_me.status_code == 200
    assert res_me.json()["current_latitude"] == 12.9300


def test_order_creation_and_tracking(client, auth_tokens):
    """Test order intake, automatic package tracking generation, and public tracking."""
    cust_headers = auth_tokens["customer"]
    admin_headers = auth_tokens["admin"]

    # Create Warehouse first
    wh_res = client.post(
        "/api/v1/warehouses",
        json={
            "name": "Central Hub",
            "code": "WH-CTR-01",
            "address_line1": "Main Road",
            "city": "Bengaluru",
            "state": "Karnataka",
            "postal_code": "560001",
            "latitude": 12.9716,
            "longitude": 77.5946,
        },
        headers=admin_headers,
    )
    wh_id = wh_res.json()["id"]

    # Create Order
    order_payload = {
        "warehouse_id": wh_id,
        "destination_address": "Flat 302, Palm Heights, Bellandur",
        "destination_city": "Bengaluru",
        "destination_state": "Karnataka",
        "destination_postal_code": "560103",
        "destination_latitude": 12.9260,
        "destination_longitude": 77.6762,
        "priority": "HIGH",
        "package": {
            "weight_kg": 6.5,
            "length_cm": 30.0,
            "width_cm": 20.0,
            "height_cm": 15.0,
            "category": "ELECTRONICS",
            "is_fragile": True,
            "requires_cold_storage": False,
        },
    }
    res_ord = client.post("/api/v1/orders", json=order_payload, headers=cust_headers)
    assert res_ord.status_code == 201, res_ord.text
    ord_data = res_ord.json()
    assert ord_data["order_number"].startswith("ORD-")
    assert ord_data["package"]["tracking_number"].startswith("TRK-")
    assert ord_data["estimated_distance_km"] > 0
    assert ord_data["estimated_delivery_cost"] > 50.0

    tracking_num = ord_data["package"]["tracking_number"]

    # Test Public Tracking Query
    res_track = client.get(f"/api/v1/orders/track/{tracking_num}")
    assert res_track.status_code == 200
    assert res_track.json()["order_number"] == ord_data["order_number"]
    assert res_track.json()["status"] == "CREATED"


def test_delivery_dispatch_and_state_machine(client, auth_tokens, db_session):
    """Test delivery dispatch, state transitions, and completion via OTP verification."""
    admin_headers = auth_tokens["admin"]
    driver_headers = auth_tokens["driver"]
    driver_user = auth_tokens["users"]["driver"]

    # Setup Warehouse
    wh_res = client.post(
        "/api/v1/warehouses",
        json={
            "name": "Dispatch Hub",
            "code": "WH-DSP-01",
            "address_line1": "Ring Road",
            "city": "Bengaluru",
            "state": "Karnataka",
            "postal_code": "560002",
            "latitude": 12.9700,
            "longitude": 77.6000,
        },
        headers=admin_headers,
    )
    wh_id = wh_res.json()["id"]

    # Setup Vehicle
    veh_res = client.post(
        "/api/v1/vehicles",
        json={
            "registration_number": "KA-02-DL-8811",
            "model": "Mahindra Bolero Maxi Truck",
            "vehicle_type": "VAN",
            "max_weight_capacity_kg": 1200.0,
            "max_volume_capacity_m3": 7.0,
            "fuel_type": "DIESEL",
            "fuel_efficiency_kmpl": 12.0,
            "status": "AVAILABLE",
        },
        headers=admin_headers,
    )
    veh_id = veh_res.json()["id"]

    # Setup Driver
    drv_res = client.post(
        "/api/v1/drivers",
        json={
            "user_id": driver_user.id,
            "license_number": "DL-KA-2023-889900",
            "current_vehicle_id": veh_id,
            "status": "AVAILABLE",
        },
        headers=admin_headers,
    )
    drv_id = drv_res.json()["id"]

    # Create Order
    ord_res = client.post(
        "/api/v1/orders",
        json={
            "customer_id": auth_tokens["customer_id"],
            "warehouse_id": wh_id,
            "destination_address": "Indiranagar 100 Feet Rd",
            "destination_city": "Bengaluru",
            "destination_state": "Karnataka",
            "destination_postal_code": "560038",
            "destination_latitude": 12.9784,
            "destination_longitude": 77.6408,
            "priority": "HIGH",
            "package": {
                "weight_kg": 8.0,
                "length_cm": 25.0,
                "width_cm": 20.0,
                "height_cm": 15.0,
                "category": "MEDICAL",
            },
        },
        headers=admin_headers,
    )
    ord_id = ord_res.json()["id"]

    # 1. Dispatch Order
    dispatch_payload = {
        "order_id": ord_id,
        "driver_id": drv_id,
        "vehicle_id": veh_id,
        "warehouse_id": wh_id,
    }
    res_disp = client.post("/api/v1/deliveries/dispatch", json=dispatch_payload, headers=admin_headers)
    assert res_disp.status_code == 201, res_disp.text
    del_data = res_disp.json()
    del_id = del_data["id"]
    assert del_data["status"] == "DISPATCHED"

    # 2. Invalid Transition Check (e.g., DISPATCHED -> DELIVERED directly without IN_TRANSIT)
    res_bad = client.post(
        f"/api/v1/deliveries/{del_id}/status",
        json={"to_status": "DELIVERED"},
        headers=driver_headers,
    )
    assert res_bad.status_code == 400

    # 3. Valid Transition: DISPATCHED -> IN_TRANSIT
    res_trans1 = client.post(
        f"/api/v1/deliveries/{del_id}/status",
        json={"to_status": "IN_TRANSIT", "notes": "Picked up from staging bay"},
        headers=driver_headers,
    )
    assert res_trans1.status_code == 200
    assert res_trans1.json()["status"] == "IN_TRANSIT"

    # 4. Valid Transition: IN_TRANSIT -> OUT_FOR_DELIVERY
    res_trans2 = client.post(
        f"/api/v1/deliveries/{del_id}/status",
        json={"to_status": "OUT_FOR_DELIVERY", "notes": "Approaching customer street"},
        headers=driver_headers,
    )
    assert res_trans2.status_code == 200
    assert res_trans2.json()["status"] == "OUT_FOR_DELIVERY"

    # 5. OTP Verification with Invalid Code
    res_wrong_otp = client.post(
        f"/api/v1/deliveries/{del_id}/verify-otp",
        json={"otp_code": "000000"},
        headers=driver_headers,
    )
    assert res_wrong_otp.status_code == 400

    # Retrieve actual OTP directly from DB
    del_obj = db_session.query(Delivery).filter(Delivery.id == del_id).first()
    assert del_obj is not None
    actual_otp = del_obj.otp_code

    # 6. OTP Verification with Correct Code
    res_verify = client.post(
        f"/api/v1/deliveries/{del_id}/verify-otp",
        json={"otp_code": actual_otp, "notes": "Handed to recipient in person"},
        headers=driver_headers,
    )
    assert res_verify.status_code == 200
    assert res_verify.json()["status"] == "DELIVERED"
    assert res_verify.json()["actual_delivery_time"] is not None
