import pytest
from backend.app.models.user import User
from backend.app.models.warehouse import Warehouse
from backend.app.models.vehicle import Vehicle
from backend.app.models.driver import Driver
from backend.app.models.order import Order
from backend.app.models.package import Package
from backend.app.models.enums import (
    UserRole,
    DriverStatus,
    VehicleStatus,
    VehicleType,
    OrderStatus,
    DeliveryPriority,
)
from backend.app.core.security import get_password_hash, create_access_token
from backend.app.intelligence.assignment import DriverAssignmentEngine
from backend.app.intelligence.routing import RouteOptimizationEngine
from backend.app.intelligence.cost import CostEstimationEngine
from backend.app.schemas.intelligence import CostEstimationRequest, StopPoint


@pytest.fixture
def intelligence_test_data(db_session):
    """Provisions test users, warehouse, vehicles, and drivers with diverse metrics."""
    # Manager
    manager = User(
        email="wh_manager@ildo.com",
        hashed_password=get_password_hash("ManagerPass123!"),
        full_name="Hub Manager",
        role=UserRole.WAREHOUSE_MANAGER,
        is_active=True,
    )
    # Driver 1: Top candidate (EV, near warehouse, 5.0 rating, 0 active)
    driver_user1 = User(
        email="top_driver@ildo.com",
        hashed_password=get_password_hash("DriverPass123!"),
        full_name="Top Performer Driver",
        role=UserRole.DRIVER,
        is_active=True,
    )
    # Driver 2: Farther away, Petrol bike, 4.2 rating, 1 active
    driver_user2 = User(
        email="busy_driver@ildo.com",
        hashed_password=get_password_hash("DriverPass123!"),
        full_name="Busy Distant Driver",
        role=UserRole.DRIVER,
        is_active=True,
    )
    # Driver 3: Offline (ineligible)
    driver_user3 = User(
        email="offline_driver@ildo.com",
        hashed_password=get_password_hash("DriverPass123!"),
        full_name="Offline Driver",
        role=UserRole.DRIVER,
        is_active=True,
    )
    db_session.add_all([manager, driver_user1, driver_user2, driver_user3])
    db_session.flush()

    # Warehouse: Bengaluru Central (12.9716, 77.5946)
    wh = Warehouse(
        name="Central Staging Hub",
        code="WH-INTEL-01",
        address_line1="Outer Ring Rd",
        city="Bengaluru",
        state="Karnataka",
        postal_code="560001",
        latitude=12.9716,
        longitude=77.5946,
        capacity_sqft=25000.0,
    )
    db_session.add(wh)
    db_session.flush()

    # Vehicles
    v1 = Vehicle(
        registration_number="KA-01-INTEL-EV",
        model="Tata Ace EV",
        vehicle_type=VehicleType.ELECTRIC_VAN,
        max_weight_capacity_kg=1000.0,
        max_volume_capacity_m3=6.0,
        fuel_type="ELECTRIC",
        status=VehicleStatus.AVAILABLE,
    )
    v2 = Vehicle(
        registration_number="KA-02-INTEL-BK",
        model="Ather Cargo Bike",
        vehicle_type=VehicleType.BIKE,
        max_weight_capacity_kg=35.0,
        max_volume_capacity_m3=0.3,
        fuel_type="PETROL",
        status=VehicleStatus.AVAILABLE,
    )
    db_session.add_all([v1, v2])
    db_session.flush()

    # Drivers
    d1 = Driver(
        user_id=driver_user1.id,
        license_number="DL-INTEL-001",
        current_vehicle_id=v1.id,
        status=DriverStatus.AVAILABLE,
        current_latitude=12.9730,  # ~200 meters from warehouse
        current_longitude=77.5960,
        rating=4.95,
        total_deliveries_completed=150,
        total_deliveries_failed=1,
        active_deliveries_count=0,
    )
    d2 = Driver(
        user_id=driver_user2.id,
        license_number="DL-INTEL-002",
        current_vehicle_id=v2.id,
        status=DriverStatus.BUSY,
        current_latitude=12.8500,  # ~15 km away
        current_longitude=77.6600,
        rating=4.30,
        total_deliveries_completed=40,
        total_deliveries_failed=4,
        active_deliveries_count=1,
    )
    d3 = Driver(
        user_id=driver_user3.id,
        license_number="DL-INTEL-003",
        current_vehicle_id=None,
        status=DriverStatus.OFFLINE,
        rating=4.50,
    )
    db_session.add_all([d1, d2, d3])
    db_session.commit()

    return {
        "manager_token": {"Authorization": f"Bearer {create_access_token(manager.id, manager.role.value)}"},
        "warehouse": wh,
        "drivers": [d1, d2, d3],
        "vehicles": [v1, v2],
    }


def test_driver_assignment_engine_unit(db_session, intelligence_test_data):
    """Direct unit testing of DriverAssignmentEngine constraint checks and mathematical scoring."""
    wh = intelligence_test_data["warehouse"]
    d1, d2, d3 = intelligence_test_data["drivers"]

    # Create dummy Order with heavy package (50kg)
    order = Order(
        order_number="ORD-UNIT-TEST",
        customer_id=1,
        warehouse_id=wh.id,
        destination_address="Koramangala 4th Block",
        destination_city="Bengaluru",
        destination_state="Karnataka",
        destination_postal_code="560034",
        destination_latitude=12.9352,
        destination_longitude=77.6245,
    )
    db_session.add(order)
    db_session.flush()

    pkg = Package(
        order_id=order.id,
        tracking_number="TRK-UNIT-01",
        weight_kg=50.0,  # Exceeds Bike capacity (35kg), fits EV (1000kg)
        volume_m3=0.05,
    )
    db_session.add(pkg)
    db_session.commit()

    # Evaluate Driver 1 (EV, near, high rating) -> Should be eligible and score very high (>85)
    is_elig1, rejections1, score1, breakdown1, rationale1 = DriverAssignmentEngine.evaluate_driver(d1, order, wh)
    assert is_elig1 is True
    assert len(rejections1) == 0
    assert score1 >= 80.0
    assert breakdown1.proximity_score >= 95.0
    assert breakdown1.workload_score == 100.0

    # Evaluate Driver 2 (Bike, capacity 35kg < 50kg) -> Should be ineligible due to payload constraint
    is_elig2, rejections2, score2, _, _ = DriverAssignmentEngine.evaluate_driver(d2, order, wh)
    assert is_elig2 is False
    assert any("exceeds vehicle payload limit" in r for r in rejections2)
    assert score2 == 0.0

    # Evaluate Driver 3 (Offline) -> Ineligible
    is_elig3, rejections3, score3, _, _ = DriverAssignmentEngine.evaluate_driver(d3, order, wh)
    assert is_elig3 is False
    assert any("OFFLINE" in r for r in rejections3)


def test_recommend_and_auto_assign_api(client, db_session, intelligence_test_data):
    """Integration test verifying GET /recommend-driver and POST /auto-assign endpoints."""
    headers = intelligence_test_data["manager_token"]
    wh = intelligence_test_data["warehouse"]

    # Create Order
    order = Order(
        order_number="ORD-API-TEST-01",
        customer_id=1,
        warehouse_id=wh.id,
        destination_address="Whitefield Tech Zone",
        destination_city="Bengaluru",
        destination_state="Karnataka",
        destination_postal_code="560066",
        destination_latitude=12.9698,
        destination_longitude=77.7500,
        status=OrderStatus.CREATED,
    )
    db_session.add(order)
    db_session.flush()

    pkg = Package(
        order_id=order.id,
        tracking_number="TRK-API-TEST",
        weight_kg=15.0,
        volume_m3=0.015,
    )
    db_session.add(pkg)
    db_session.commit()

    # 1. Query Driver Recommendations
    res_rec = client.get(f"/api/v1/intelligence/recommend-driver/{order.id}", headers=headers)
    assert res_rec.status_code == 200, res_rec.text
    rec_data = res_rec.json()
    assert rec_data["order_id"] == order.id
    assert rec_data["evaluated_candidates_count"] >= 3
    assert rec_data["eligible_candidates_count"] >= 1
    assert rec_data["candidates"][0]["recommendation_rank"] == 1
    assert rec_data["candidates"][0]["is_eligible"] is True

    # Top candidate should be Top Performer Driver
    top_cand = rec_data["candidates"][0]
    assert top_cand["driver_name"] == "Top Performer Driver"

    # 2. Execute Auto-Assign
    res_assign = client.post(f"/api/v1/intelligence/auto-assign/{order.id}", headers=headers)
    assert res_assign.status_code == 201, res_assign.text
    assign_data = res_assign.json()
    assert assign_data["status"] == "success"
    assert assign_data["delivery_number"].startswith("DEL-")
    assert assign_data["assigned_driver_name"] == "Top Performer Driver"
    assert len(assign_data["otp_code"]) == 6

    # Verify Order is now DISPATCHED
    res_order = client.get(f"/api/v1/orders/{order.id}", headers=headers)
    assert res_order.json()["status"] == "DISPATCHED"


def test_dijkstra_route_optimization_endpoint(client, intelligence_test_data):
    """Test Dijkstra shortest path calculation on waypoint graph."""
    headers = intelligence_test_data["manager_token"]

    payload = {
        "origin_latitude": 12.9716,
        "origin_longitude": 77.5946,
        "destination_latitude": 12.9352,
        "destination_longitude": 77.6245,
        "origin_name": "Bengaluru Central Depot",
        "destination_name": "Koramangala Hub",
    }
    res = client.post("/api/v1/intelligence/optimize-route", json=payload, headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["straight_line_distance_km"] > 0
    assert data["network_distance_km"] >= data["straight_line_distance_km"]
    assert len(data["path_nodes"]) >= 3
    assert len(data["legs"]) >= 2
    assert "Dijkstra" in data["algorithm_used"]


def test_multi_stop_tsp_endpoint(client, intelligence_test_data):
    """Test multi-stop TSP Nearest-Neighbor heuristic routing."""
    headers = intelligence_test_data["manager_token"]

    payload = {
        "depot_latitude": 12.9716,
        "depot_longitude": 77.5946,
        "depot_name": "Bengaluru Main Fulfillment Hub",
        "stops": [
            {"id": "STOP-1", "label": "Indiranagar", "latitude": 12.9784, "longitude": 77.6408, "priority": "HIGH"},
            {"id": "STOP-2", "label": "Whitefield", "latitude": 12.9698, "longitude": 77.7500, "priority": "MEDIUM"},
            {"id": "STOP-3", "label": "Bellandur", "latitude": 12.9260, "longitude": 77.6762, "priority": "URGENT"},
            {"id": "STOP-4", "label": "Koramangala", "latitude": 12.9352, "longitude": 77.6245, "priority": "LOW"},
        ],
    }
    res = client.post("/api/v1/intelligence/optimize-multi-stop", json=payload, headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["total_stops"] == 4
    assert data["total_route_distance_km"] > 0
    assert len(data["optimized_stop_sequence"]) == 4
    assert len(data["route_legs"]) == 4
    # URGENT / HIGH priority stop should be prioritized earlier in the sequence
    first_two_stops = [s["id"] for s in data["optimized_stop_sequence"][:2]]
    assert "STOP-1" in first_two_stops or "STOP-3" in first_two_stops


def test_transparent_cost_estimation_endpoint(client, intelligence_test_data):
    """Test itemized transparent operating cost calculation."""
    headers = intelligence_test_data["manager_token"]

    payload = {
        "distance_km": 25.0,
        "package_weight_kg": 18.5,
        "vehicle_type": "ELECTRIC_VAN",
        "priority": "HIGH",
        "requires_cold_storage": True,
    }
    res = client.post("/api/v1/intelligence/estimate-cost", json=payload, headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["distance_km"] == 25.0
    assert data["fuel_expense_inr"] > 0
    assert data["driver_labor_inr"] > 0
    assert data["vehicle_maintenance_inr"] > 0
    assert data["cold_storage_surcharge_inr"] > 0
    assert data["priority_surcharge_inr"] > 0
    assert data["tax_gst_inr"] > 0
    assert data["total_estimated_cost_inr"] > data["subtotal_inr"]

    # Verify line items cover all categories
    categories = [item["category"] for item in data["line_items"]]
    assert "BASE" in categories
    assert "FUEL" in categories
    assert "LABOR" in categories
    assert "MAINTENANCE" in categories
    assert "COLD_STORAGE" in categories
    assert "PRIORITY" in categories
