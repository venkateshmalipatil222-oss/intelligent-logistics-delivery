import pytest
from datetime import datetime, timezone, timedelta
from backend.app.models.warehouse import Warehouse
from backend.app.models.vehicle import Vehicle
from backend.app.models.driver import Driver
from backend.app.models.order import Order
from backend.app.models.package import Package
from backend.app.models.delivery import Delivery
from backend.app.models.enums import (
    VehicleType,
    VehicleStatus,
    DriverStatus,
    OrderStatus,
    DeliveryPriority,
    DeliveryFailureReason,
)


@pytest.fixture
def analytics_seed_data(db_session, auth_tokens):
    """Seed sample warehouses, vehicles, drivers, and orders for analytics verification."""
    now = datetime.now(timezone.utc)

    # 1. Warehouses
    wh1 = Warehouse(
        name="Electronic City Cross-Dock Hub",
        code="WH-BLR-EC01",
        address_line1="Phase 1, Hosur Road",
        city="Bengaluru",
        state="Karnataka",
        postal_code="560100",
        latitude=12.8452,
        longitude=77.6602,
        capacity_sqft=12000.0,
        is_active=True,
    )
    wh2 = Warehouse(
        name="Whitefield Fulfillment Center",
        code="WH-BLR-WF02",
        address_line1="ITPB Main Road",
        city="Bengaluru",
        state="Karnataka",
        postal_code="560066",
        latitude=12.9856,
        longitude=77.7374,
        capacity_sqft=18000.0,
        is_active=True,
    )
    db_session.add_all([wh1, wh2])
    db_session.flush()

    # 2. Vehicles
    v_ev = Vehicle(
        registration_number="KA-01-EV-1001",
        model="Tata Ace EV",
        vehicle_type=VehicleType.ELECTRIC_VAN,
        max_weight_capacity_kg=1000.0,
        max_volume_capacity_m3=6.0,
        fuel_type="ELECTRIC",
        fuel_efficiency_kmpl=20.0,
        status=VehicleStatus.IN_SERVICE,
    )
    v_diesel = Vehicle(
        registration_number="KA-01-DS-2002",
        model="Mahindra Bolero Maxi Truck",
        vehicle_type=VehicleType.VAN,
        max_weight_capacity_kg=1200.0,
        max_volume_capacity_m3=7.0,
        fuel_type="DIESEL",
        fuel_efficiency_kmpl=12.0,
        status=VehicleStatus.AVAILABLE,
    )
    db_session.add_all([v_ev, v_diesel])
    db_session.flush()

    # 3. Driver
    driver = Driver(
        user_id=auth_tokens["users"]["driver"].id,
        license_number="DL-BLR-2026-9999",
        current_vehicle_id=v_ev.id,
        status=DriverStatus.BUSY,
        current_latitude=12.8500,
        current_longitude=77.6650,
        total_deliveries_completed=14,
        total_deliveries_failed=1,
        rating=4.9,
        active_deliveries_count=1,
    )
    db_session.add(driver)
    db_session.flush()

    # 4. Orders
    cust_id = auth_tokens["customer_id"]

    # Order 1: Delivered On-Time
    ord_del = Order(
        order_number="ORD-TEST-ANALYTICS-01",
        customer_id=cust_id,
        warehouse_id=wh1.id,
        destination_address="Koramangala 4th Block",
        destination_city="Bengaluru",
        destination_state="Karnataka",
        destination_postal_code="560034",
        destination_latitude=12.9352,
        destination_longitude=77.6245,
        priority=DeliveryPriority.HIGH,
        status=OrderStatus.DELIVERED,
        estimated_distance_km=14.5,
        estimated_delivery_cost=245.0,
        promised_delivery_time=now + timedelta(hours=2),
    )
    db_session.add(ord_del)
    db_session.flush()

    del1 = Delivery(
        delivery_number="DEL-TEST-ANALYTICS-01",
        order_id=ord_del.id,
        driver_id=driver.id,
        vehicle_id=v_ev.id,
        warehouse_id=wh1.id,
        status=OrderStatus.DELIVERED,
        dispatched_at=now - timedelta(minutes=45),
        actual_delivery_time=now - timedelta(minutes=10),
        otp_code="123456",
    )
    db_session.add(del1)

    # Order 2: Ready for dispatch in Hub
    ord_ready = Order(
        order_number="ORD-TEST-ANALYTICS-02",
        customer_id=cust_id,
        warehouse_id=wh1.id,
        destination_address="HSR Layout Sector 2",
        destination_city="Bengaluru",
        destination_state="Karnataka",
        destination_postal_code="560102",
        destination_latitude=12.9121,
        destination_longitude=77.6446,
        priority=DeliveryPriority.URGENT,
        status=OrderStatus.READY_FOR_DISPATCH,
        estimated_distance_km=8.2,
        estimated_delivery_cost=180.0,
    )
    db_session.add(ord_ready)
    db_session.flush()

    pkg_ready = Package(
        order_id=ord_ready.id,
        tracking_number="TRK-TEST-READY-01",
        weight_kg=2.5,
        is_ready_for_dispatch=True,
    )
    db_session.add(pkg_ready)

    # Order 3: Failed Delivery
    ord_fail = Order(
        order_number="ORD-TEST-ANALYTICS-03",
        customer_id=cust_id,
        warehouse_id=wh2.id,
        destination_address="Indiranagar 100ft Road",
        destination_city="Bengaluru",
        destination_state="Karnataka",
        destination_postal_code="560038",
        destination_latitude=12.9719,
        destination_longitude=77.6412,
        priority=DeliveryPriority.MEDIUM,
        status=OrderStatus.FAILED,
        estimated_distance_km=18.0,
        estimated_delivery_cost=310.0,
    )
    db_session.add(ord_fail)
    db_session.flush()

    del_fail = Delivery(
        delivery_number="DEL-TEST-ANALYTICS-03",
        order_id=ord_fail.id,
        driver_id=driver.id,
        vehicle_id=v_diesel.id,
        warehouse_id=wh2.id,
        status=OrderStatus.FAILED,
        dispatched_at=now - timedelta(hours=1),
        failed_at=now - timedelta(minutes=20),
        failure_reason=DeliveryFailureReason.RECIPIENT_UNAVAILABLE.value,
    )
    db_session.add(del_fail)

    db_session.commit()
    return {
        "wh1": wh1,
        "wh2": wh2,
        "driver": driver,
        "vehicle_ev": v_ev,
        "vehicle_diesel": v_diesel,
    }


def test_analytics_overview_admin_success(client, auth_tokens, analytics_seed_data):
    """Verify Admin can retrieve operational analytics overview with SLA and fleet breakdown."""
    response = client.get("/api/v1/analytics/overview", headers=auth_tokens["admin"])
    assert response.status_code == 200
    data = response.json()

    assert data["total_orders"] >= 3
    assert data["total_deliveries"] >= 2
    assert data["completed_deliveries"] >= 1
    assert data["failed_deliveries"] >= 1
    assert isinstance(data["sla_on_time_rate_pct"], (int, float))
    assert 0.0 <= data["sla_on_time_rate_pct"] <= 100.0
    assert data["total_revenue_inr"] > 0.0

    # Fleet summary checks
    fleet = data["fleet_summary"]
    assert fleet["total_vehicles"] >= 2
    assert fleet["ev_count"] >= 1
    assert fleet["diesel_count"] >= 1
    assert fleet["electric_percentage"] >= 50.0

    # Driver workforce checks
    drv_summary = data["driver_summary"]
    assert drv_summary["total_drivers"] >= 1
    assert drv_summary["average_driver_rating"] >= 4.0

    # Failure breakdown check
    assert DeliveryFailureReason.RECIPIENT_UNAVAILABLE.value in data["failure_reasons_summary"]


def test_analytics_overview_warehouse_manager_success(client, auth_tokens, analytics_seed_data):
    """Verify Warehouse Manager has access to analytics overview."""
    response = client.get("/api/v1/analytics/overview", headers=auth_tokens["manager"])
    assert response.status_code == 200
    assert "total_orders" in response.json()


def test_analytics_overview_rbac_forbidden_for_customer(client, auth_tokens, analytics_seed_data):
    """Verify Customers and unauthenticated users cannot access operational analytics."""
    # Customer RBAC rejection
    cust_res = client.get("/api/v1/analytics/overview", headers=auth_tokens["customer"])
    assert cust_res.status_code == 403

    # Unauthenticated access rejection
    unauth_res = client.get("/api/v1/analytics/overview")
    assert unauth_res.status_code == 401


def test_driver_leaderboard_endpoint(client, auth_tokens, analytics_seed_data):
    """Verify Driver Leaderboard returns ranked drivers with composite performance metrics."""
    response = client.get("/api/v1/analytics/driver-leaderboard?limit=10", headers=auth_tokens["admin"])
    assert response.status_code == 200
    data = response.json()

    assert "total_ranked_drivers" in data
    assert len(data["drivers"]) >= 1

    top_driver = data["drivers"][0]
    assert top_driver["rank"] == 1
    assert top_driver["rating"] >= 4.5
    assert top_driver["total_deliveries_completed"] >= 14
    assert top_driver["on_time_rate_pct"] > 0
    assert "assigned_vehicle_registration" in top_driver


def test_warehouse_utilization_endpoint(client, auth_tokens, analytics_seed_data):
    """Verify Warehouse Utilization endpoint returns capacity metrics and staging package counts."""
    response = client.get("/api/v1/analytics/warehouse-utilization", headers=auth_tokens["manager"])
    assert response.status_code == 200
    data = response.json()

    assert data["total_warehouses"] >= 2
    assert data["total_network_capacity_sqft"] >= 30000.0
    assert 0.0 <= data["average_utilization_rate_pct"] <= 100.0

    # Verify individual warehouse object
    wh_items = data["warehouses"]
    target_wh = next((w for w in wh_items if w["warehouse_code"] == "WH-BLR-EC01"), None)
    assert target_wh is not None
    assert target_wh["capacity_sqft"] == 12000.0
    assert target_wh["staged_packages_count"] >= 1
    assert target_wh["status_level"] in ["NORMAL", "ELEVATED", "CRITICAL"]
    assert target_wh["available_capacity_sqft"] > 0.0


def test_customer_cost_estimation_endpoint(client, auth_tokens):
    """Verify transparent delivery cost estimation tool computes fuel, labor, and GST line items."""
    payload = {
        "distance_km": 25.0,
        "package_weight_kg": 4.5,
        "vehicle_type": "VAN",
        "priority": "HIGH",
        "requires_cold_storage": True,
    }
    response = client.post("/api/v1/intelligence/estimate-cost", json=payload, headers=auth_tokens["customer"])
    assert response.status_code == 200
    data = response.json()

    assert data["distance_km"] == 25.0
    assert data["package_weight_kg"] == 4.5
    assert data["subtotal_inr"] > 0.0
    assert data["tax_gst_inr"] == pytest.approx(round(data["subtotal_inr"] * 0.18, 2), abs=0.1)
    assert data["total_estimated_cost_inr"] == pytest.approx(data["subtotal_inr"] + data["tax_gst_inr"], abs=0.1)
    assert len(data["line_items"]) >= 4
    assert "Subtotal" in data["calculation_explanation"]
    assert "GST" in data["calculation_explanation"]
