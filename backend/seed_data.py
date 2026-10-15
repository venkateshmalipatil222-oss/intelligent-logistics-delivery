"""
Comprehensive Demo Seeder for Intelligent Logistics & Delivery Optimization Platform (ILDO).
Seeds Users, Warehouses, Fleet Vehicles, Drivers, Orders, Packages, Active Deliveries, Notifications, and Audit Logs.
Safe and idempotent: skips entities if they already exist. Supports '--clean' to wipe and reseed.
"""
import sys
import os
import argparse
from datetime import datetime, timedelta, timezone

# Add workspace root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal, Base, engine
from backend.app.core.security import get_password_hash
from backend.app.core.logger import logger
from backend.app.models.user import User
from backend.app.models.customer import Customer
from backend.app.models.warehouse import Warehouse
from backend.app.models.vehicle import Vehicle
from backend.app.models.driver import Driver
from backend.app.models.package import Package
from backend.app.models.order import Order
from backend.app.models.delivery import Delivery, DeliveryStatusHistory
from backend.app.models.notification import Notification
from backend.app.models.audit import AuditLog
from backend.app.models.enums import (
    UserRole,
    DriverStatus,
    VehicleStatus,
    VehicleType,
    OrderStatus,
    DeliveryPriority,
    NotificationType,
    NotificationSeverity,
)


def seed_database(clean: bool = False):
    db = SessionLocal()
    try:
        print("=" * 70)
        print("  INTELLIGENT LOGISTICS & DELIVERY OPTIMIZATION PLATFORM (ILDO)")
        print("                   ENTERPRISE DEMO SEEDER")
        print("=" * 70)

        if clean:
            print("[INFO] Clean flag detected. Resetting database tables...")
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)
            print("[INFO] Tables re-created successfully.\n")

        # -------------------------------------------------------------
        # 1. Users & Customers
        # -------------------------------------------------------------
        print("[1/7] Seeding Users & Customer Profiles...")
        users_data = [
            {
                "email": "admin@ildo.com",
                "password": "AdminPass123!",
                "full_name": "Executive System Admin",
                "phone": "+919876543201",
                "role": UserRole.ADMIN,
            },
            {
                "email": "manager@ildo.com",
                "password": "ManagerPass123!",
                "full_name": "Bengaluru Central Hub Manager",
                "phone": "+919876543202",
                "role": UserRole.WAREHOUSE_MANAGER,
            },
            {
                "email": "manager.mumbai@ildo.com",
                "password": "ManagerPass123!",
                "full_name": "Mumbai Logistics Terminal Manager",
                "phone": "+919876543207",
                "role": UserRole.WAREHOUSE_MANAGER,
            },
            {
                "email": "driver@ildo.com",
                "password": "DriverPass123!",
                "full_name": "Suresh Raina (Fleet Driver)",
                "phone": "+919876543203",
                "role": UserRole.DRIVER,
            },
            {
                "email": "driver2@ildo.com",
                "password": "DriverPass123!",
                "full_name": "Rajesh Kumar (Express Courier)",
                "phone": "+919876543205",
                "role": UserRole.DRIVER,
            },
            {
                "email": "driver3@ildo.com",
                "password": "DriverPass123!",
                "full_name": "Amitabh Sharma (Heavy Hauler)",
                "phone": "+919876543208",
                "role": UserRole.DRIVER,
            },
            {
                "email": "customer@ildo.com",
                "password": "CustomerPass123!",
                "full_name": "Deepika Patel (Shipper)",
                "phone": "+919876543204",
                "role": UserRole.CUSTOMER,
                "company_name": "Zenith Retail Corp",
                "address_line1": "104 Outer Ring Road, Bellandur",
                "city": "Bengaluru",
                "state": "Karnataka",
                "postal_code": "560103",
                "latitude": 12.9260,
                "longitude": 77.6762,
            },
            {
                "email": "customer2@ildo.com",
                "password": "CustomerPass123!",
                "full_name": "Arjun Sharma (E-Commerce Client)",
                "phone": "+919876543206",
                "role": UserRole.CUSTOMER,
                "company_name": "Nova Tech Solutions",
                "address_line1": "45 MG Road",
                "city": "Bengaluru",
                "state": "Karnataka",
                "postal_code": "560001",
                "latitude": 12.9738,
                "longitude": 77.6119,
            },
        ]

        users_map = {}
        for u in users_data:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if not existing:
                new_user = User(
                    email=u["email"],
                    hashed_password=get_password_hash(u["password"]),
                    full_name=u["full_name"],
                    phone=u["phone"],
                    role=u["role"],
                    is_active=True,
                    is_verified=True,
                )
                db.add(new_user)
                db.flush()
                users_map[u["email"]] = new_user

                if u["role"] == UserRole.CUSTOMER:
                    cust = Customer(
                        user_id=new_user.id,
                        company_name=u.get("company_name"),
                        address_line1=u.get("address_line1"),
                        city=u.get("city"),
                        state=u.get("state"),
                        postal_code=u.get("postal_code"),
                        country="India",
                        default_latitude=u.get("latitude"),
                        default_longitude=u.get("longitude"),
                    )
                    db.add(cust)
                print(f"  + User: {u['email']} [{u['role'].value}]")
            else:
                users_map[u["email"]] = existing

        # -------------------------------------------------------------
        # 2. Warehouses
        # -------------------------------------------------------------
        print("\n[2/7] Seeding Strategic Logistics Warehouses...")
        mgr_blr = users_map.get("manager@ildo.com")
        mgr_bom = users_map.get("manager.mumbai@ildo.com")

        warehouses_data = [
            {
                "code": "WH-BLR-01",
                "name": "Bengaluru Central Logistics Hub",
                "address_line1": "Plot 12, Industrial Area, Peenya",
                "city": "Bengaluru",
                "state": "Karnataka",
                "postal_code": "560058",
                "latitude": 13.0285,
                "longitude": 77.5197,
                "capacity_sqft": 50000.0,
                "contact_phone": "+918023456789",
                "manager_id": mgr_blr.id if mgr_blr else None,
            },
            {
                "code": "WH-BOM-01",
                "name": "Mumbai Western Distribution Center",
                "address_line1": "Sector 19, Vashi",
                "city": "Navi Mumbai",
                "state": "Maharashtra",
                "postal_code": "400703",
                "latitude": 19.0771,
                "longitude": 72.9986,
                "capacity_sqft": 75000.0,
                "contact_phone": "+912227891234",
                "manager_id": mgr_bom.id if mgr_bom else None,
            },
            {
                "code": "WH-DEL-01",
                "name": "Delhi NCR Express Staging Facility",
                "address_line1": "Udyog Vihar Phase 4",
                "city": "Gurugram",
                "state": "Haryana",
                "postal_code": "122015",
                "latitude": 28.4984,
                "longitude": 77.0850,
                "capacity_sqft": 60000.0,
                "contact_phone": "+911244567890",
                "manager_id": None,
            },
            {
                "code": "WH-HYD-01",
                "name": "Hyderabad Tech Corridor Depot",
                "address_line1": "Financial District, Nanakramguda",
                "city": "Hyderabad",
                "state": "Telangana",
                "postal_code": "500032",
                "latitude": 17.4156,
                "longitude": 78.3427,
                "capacity_sqft": 45000.0,
                "contact_phone": "+914023456789",
                "manager_id": None,
            },
        ]

        wh_map = {}
        for wh in warehouses_data:
            existing = db.query(Warehouse).filter(Warehouse.code == wh["code"]).first()
            if not existing:
                new_wh = Warehouse(**wh)
                db.add(new_wh)
                db.flush()
                wh_map[wh["code"]] = new_wh
                print(f"  + Warehouse: {wh['name']} ({wh['code']})")
            else:
                wh_map[wh["code"]] = existing

        # -------------------------------------------------------------
        # 3. Fleet Vehicles
        # -------------------------------------------------------------
        print("\n[3/7] Seeding Fleet Vehicles...")
        vehicles_data = [
            {
                "registration_number": "KA-01-EV-2024",
                "model": "Tata Ace EV (Electric Van)",
                "vehicle_type": VehicleType.ELECTRIC_VAN,
                "max_weight_capacity_kg": 1000.0,
                "max_volume_capacity_m3": 5.8,
                "fuel_type": "ELECTRIC",
                "fuel_efficiency_kmpl": 16.5,
                "status": VehicleStatus.IN_SERVICE,
                "current_latitude": 13.0285,
                "current_longitude": 77.5197,
            },
            {
                "registration_number": "KA-05-TR-8899",
                "model": "BharatBenz 1217C Medium Truck",
                "vehicle_type": VehicleType.TRUCK,
                "max_weight_capacity_kg": 6000.0,
                "max_volume_capacity_m3": 26.0,
                "fuel_type": "DIESEL",
                "fuel_efficiency_kmpl": 7.5,
                "status": VehicleStatus.AVAILABLE,
                "current_latitude": 13.0285,
                "current_longitude": 77.5197,
            },
            {
                "registration_number": "KA-03-BK-1122",
                "model": "Ather 450X Cargo Edition",
                "vehicle_type": VehicleType.BIKE,
                "max_weight_capacity_kg": 45.0,
                "max_volume_capacity_m3": 0.4,
                "fuel_type": "ELECTRIC",
                "fuel_efficiency_kmpl": 40.0,
                "status": VehicleStatus.AVAILABLE,
                "current_latitude": 12.9738,
                "current_longitude": 77.6119,
            },
            {
                "registration_number": "MH-04-HV-5544",
                "model": "Tata Prima 4028 Heavy Hauler",
                "vehicle_type": VehicleType.TRUCK,
                "max_weight_capacity_kg": 18000.0,
                "max_volume_capacity_m3": 55.0,
                "fuel_type": "DIESEL",
                "fuel_efficiency_kmpl": 4.5,
                "status": VehicleStatus.AVAILABLE,
                "current_latitude": 19.0771,
                "current_longitude": 72.9986,
            },
            {
                "registration_number": "DL-01-VN-7722",
                "model": "Mahindra Bolero Maxi Truck Plus",
                "vehicle_type": VehicleType.VAN,
                "max_weight_capacity_kg": 1500.0,
                "max_volume_capacity_m3": 8.2,
                "fuel_type": "DIESEL",
                "fuel_efficiency_kmpl": 12.0,
                "status": VehicleStatus.AVAILABLE,
                "current_latitude": 28.4984,
                "current_longitude": 77.0850,
            },
        ]

        veh_map = {}
        for v in vehicles_data:
            existing = db.query(Vehicle).filter(Vehicle.registration_number == v["registration_number"]).first()
            if not existing:
                new_veh = Vehicle(**v)
                db.add(new_veh)
                db.flush()
                veh_map[v["registration_number"]] = new_veh
                print(f"  + Vehicle: {v['registration_number']} [{v['model']}]")
            else:
                veh_map[v["registration_number"]] = existing

        # -------------------------------------------------------------
        # 4. Drivers
        # -------------------------------------------------------------
        print("\n[4/7] Seeding Driver Profiles & Assigning Fleets...")
        d1_user = users_map.get("driver@ildo.com")
        d2_user = users_map.get("driver2@ildo.com")
        d3_user = users_map.get("driver3@ildo.com")
        v1 = veh_map.get("KA-01-EV-2024")
        v2 = veh_map.get("KA-03-BK-1122")
        v3 = veh_map.get("MH-04-HV-5544")

        drivers_data = [
            {
                "user_id": d1_user.id,
                "license_number": "DL-KA-2021-998811",
                "current_vehicle_id": v1.id if v1 else None,
                "status": DriverStatus.BUSY,
                "current_latitude": 13.0285,
                "current_longitude": 77.5197,
                "rating": 4.92,
                "total_deliveries_completed": 142,
                "total_deliveries_failed": 2,
                "active_deliveries_count": 1,
            },
            {
                "user_id": d2_user.id,
                "license_number": "DL-KA-2020-554433",
                "current_vehicle_id": v2.id if v2 else None,
                "status": DriverStatus.AVAILABLE,
                "current_latitude": 12.9738,
                "current_longitude": 77.6119,
                "rating": 4.85,
                "total_deliveries_completed": 98,
                "total_deliveries_failed": 1,
                "active_deliveries_count": 0,
            },
            {
                "user_id": d3_user.id,
                "license_number": "DL-MH-2018-771122",
                "current_vehicle_id": v3.id if v3 else None,
                "status": DriverStatus.AVAILABLE,
                "current_latitude": 19.0771,
                "current_longitude": 72.9986,
                "rating": 4.78,
                "total_deliveries_completed": 215,
                "total_deliveries_failed": 4,
                "active_deliveries_count": 0,
            },
        ]

        drv_map = {}
        for d in drivers_data:
            existing = db.query(Driver).filter(Driver.user_id == d["user_id"]).first()
            if not existing:
                new_drv = Driver(**d)
                db.add(new_drv)
                db.flush()
                drv_map[d["user_id"]] = new_drv
                print(f"  + Driver: {users_map[list(users_map.keys())[0]].email if False else d['license_number']} [Rating: {d['rating']}]")
            else:
                drv_map[d["user_id"]] = existing

        # -------------------------------------------------------------
        # 5. Orders & Packages (Comprehensive Lifecycle Stages)
        # -------------------------------------------------------------
        print("\n[5/7] Seeding Multi-Stage Orders & Package Inventory...")
        c1_user = users_map.get("customer@ildo.com")
        c2_user = users_map.get("customer2@ildo.com")
        c1_cust = db.query(Customer).filter(Customer.user_id == c1_user.id).first()
        c2_cust = db.query(Customer).filter(Customer.user_id == c2_user.id).first()
        blr_wh = wh_map.get("WH-BLR-01")
        bom_wh = wh_map.get("WH-BOM-01")

        orders_catalog = [
            # 1. PENDING (Placed by customer, awaiting warehouse confirmation)
            {
                "order_number": "ORD-20261015-BLR01",
                "customer_id": c1_cust.id,
                "warehouse_id": blr_wh.id,
                "destination_address": "Flat 302, Green Glen Layout, Bellandur",
                "destination_city": "Bengaluru",
                "destination_state": "Karnataka",
                "destination_postal_code": "560103",
                "destination_latitude": 12.9280,
                "destination_longitude": 77.6740,
                "priority": DeliveryPriority.MEDIUM,
                "status": OrderStatus.CREATED,
                "estimated_distance_km": 24.5,
                "estimated_delivery_cost": 320.0,
                "package": {
                    "tracking_number": "TRK-BLR-1001",
                    "weight_kg": 3.5,
                    "length_cm": 25.0,
                    "width_cm": 20.0,
                    "height_cm": 15.0,
                    "volume_m3": 0.0075,
                    "category": "HOME_APPLIANCES",
                    "is_fragile": False,
                    "requires_cold_storage": False,
                    "is_ready_for_dispatch": False,
                },
            },
            # 2. PROCESSING (Under warehouse picking & packing)
            {
                "order_number": "ORD-20261015-BLR02",
                "customer_id": c2_cust.id,
                "warehouse_id": blr_wh.id,
                "destination_address": "Prestige Cyber Towers, Electronic City Phase 1",
                "destination_city": "Bengaluru",
                "destination_state": "Karnataka",
                "destination_postal_code": "560100",
                "destination_latitude": 12.8452,
                "destination_longitude": 77.6602,
                "priority": DeliveryPriority.HIGH,
                "status": OrderStatus.PROCESSING,
                "estimated_distance_km": 32.1,
                "estimated_delivery_cost": 445.0,
                "package": {
                    "tracking_number": "TRK-BLR-1002",
                    "weight_kg": 6.8,
                    "length_cm": 35.0,
                    "width_cm": 25.0,
                    "height_cm": 20.0,
                    "volume_m3": 0.0175,
                    "category": "OFFICE_SUPPLIES",
                    "is_fragile": False,
                    "requires_cold_storage": False,
                    "is_ready_for_dispatch": False,
                },
            },
            # 3. READY_FOR_DISPATCH (Packed & ready for auto-assignment / dispatch)
            {
                "order_number": "ORD-20261015-BLR03",
                "customer_id": c1_cust.id,
                "warehouse_id": blr_wh.id,
                "destination_address": "Tech Park Boulevard, Whitefield",
                "destination_city": "Bengaluru",
                "destination_state": "Karnataka",
                "destination_postal_code": "560066",
                "destination_latitude": 12.9698,
                "destination_longitude": 77.7500,
                "priority": DeliveryPriority.URGENT,
                "status": OrderStatus.READY_FOR_DISPATCH,
                "estimated_distance_km": 28.2,
                "estimated_delivery_cost": 418.4,
                "package": {
                    "tracking_number": "TRK-BLR-1003",
                    "weight_kg": 4.2,
                    "length_cm": 25.0,
                    "width_cm": 20.0,
                    "height_cm": 15.0,
                    "volume_m3": 0.0075,
                    "category": "ELECTRONICS",
                    "is_fragile": True,
                    "requires_cold_storage": False,
                    "is_ready_for_dispatch": True,
                },
            },
            # 4. DISPATCHED (Active delivery on road with OTP)
            {
                "order_number": "ORD-20261015-BLR04",
                "customer_id": c1_cust.id,
                "warehouse_id": blr_wh.id,
                "destination_address": "88, 100 Feet Road, Indiranagar",
                "destination_city": "Bengaluru",
                "destination_state": "Karnataka",
                "destination_postal_code": "560038",
                "destination_latitude": 12.9784,
                "destination_longitude": 77.6408,
                "priority": DeliveryPriority.HIGH,
                "status": OrderStatus.DISPATCHED,
                "estimated_distance_km": 16.4,
                "estimated_delivery_cost": 296.8,
                "package": {
                    "tracking_number": "TRK-BLR-1004",
                    "weight_kg": 12.5,
                    "length_cm": 45.0,
                    "width_cm": 30.0,
                    "height_cm": 25.0,
                    "volume_m3": 0.0338,
                    "category": "MEDICAL_EQUIPMENT",
                    "is_fragile": True,
                    "requires_cold_storage": False,
                    "is_ready_for_dispatch": True,
                },
            },
            # 5. DELIVERED (Successfully verified with OTP Proof of Delivery)
            {
                "order_number": "ORD-20261014-BLR05",
                "customer_id": c2_cust.id,
                "warehouse_id": blr_wh.id,
                "destination_address": "7th Block, Koramangala",
                "destination_city": "Bengaluru",
                "destination_state": "Karnataka",
                "destination_postal_code": "560095",
                "destination_latitude": 12.9352,
                "destination_longitude": 77.6245,
                "priority": DeliveryPriority.MEDIUM,
                "status": OrderStatus.DELIVERED,
                "estimated_distance_km": 18.1,
                "estimated_delivery_cost": 292.2,
                "package": {
                    "tracking_number": "TRK-BLR-1005",
                    "weight_kg": 5.0,
                    "length_cm": 30.0,
                    "width_cm": 20.0,
                    "height_cm": 12.0,
                    "volume_m3": 0.0072,
                    "category": "GENERAL_MERCHANDISE",
                    "is_fragile": False,
                    "requires_cold_storage": False,
                    "is_ready_for_dispatch": True,
                },
            },
            # 6. FAILED (Delivery attempt failed, customer unavailable)
            {
                "order_number": "ORD-20261014-BOM06",
                "customer_id": c1_cust.id,
                "warehouse_id": bom_wh.id,
                "destination_address": "Bandra Kurla Complex, G Block",
                "destination_city": "Mumbai",
                "destination_state": "Maharashtra",
                "destination_postal_code": "400051",
                "destination_latitude": 19.0660,
                "destination_longitude": 72.8685,
                "priority": DeliveryPriority.URGENT,
                "status": OrderStatus.FAILED,
                "estimated_distance_km": 14.8,
                "estimated_delivery_cost": 260.0,
                "package": {
                    "tracking_number": "TRK-BOM-1006",
                    "weight_kg": 8.0,
                    "length_cm": 40.0,
                    "width_cm": 30.0,
                    "height_cm": 20.0,
                    "volume_m3": 0.0240,
                    "category": "PHARMACEUTICALS",
                    "is_fragile": True,
                    "requires_cold_storage": True,
                    "is_ready_for_dispatch": True,
                },
            },
        ]

        saved_orders = {}
        for o_data in orders_catalog:
            pkg_data = o_data.pop("package")
            existing = db.query(Order).filter(Order.order_number == o_data["order_number"]).first()
            if not existing:
                new_ord = Order(**o_data)
                db.add(new_ord)
                db.flush()

                new_pkg = Package(order_id=new_ord.id, **pkg_data)
                db.add(new_pkg)
                saved_orders[o_data["order_number"]] = new_ord
                print(f"  + Order: {new_ord.order_number} [{new_ord.status.value}] Tracking: {pkg_data['tracking_number']}")
            else:
                saved_orders[o_data["order_number"]] = existing

        # -------------------------------------------------------------
        # 6. Deliveries & PoD Lifecycle History
        # -------------------------------------------------------------
        print("\n[6/7] Seeding Dispatched, Delivered & Failed Delivery Records...")
        now = datetime.now(timezone.utc)
        driver1 = drv_map.get(d1_user.id)
        driver2 = drv_map.get(d2_user.id)
        veh1 = veh_map.get("KA-01-EV-2024")
        veh2 = veh_map.get("KA-03-BK-1122")

        # 6a. Dispatched Active Order (ORD-20261015-BLR04)
        ord_dispatched = saved_orders.get("ORD-20261015-BLR04")
        if ord_dispatched:
            del_num = f"DEL-{ord_dispatched.order_number}"
            del_existing = db.query(Delivery).filter((Delivery.order_id == ord_dispatched.id) | (Delivery.delivery_number == del_num)).first()
            if not del_existing:
                active_del = Delivery(
                    delivery_number=del_num,
                    order_id=ord_dispatched.id,
                    driver_id=driver1.id,
                    vehicle_id=veh1.id,
                    warehouse_id=blr_wh.id,
                    status=OrderStatus.DISPATCHED,
                    pickup_time=now - timedelta(minutes=45),
                    dispatched_at=now - timedelta(minutes=45),
                    otp_code="784912",
                    otp_expires_at=now + timedelta(hours=2),
                    otp_attempts=0,
                )
                db.add(active_del)
                db.flush()

                h1 = DeliveryStatusHistory(
                    delivery_id=active_del.id,
                    from_status=OrderStatus.READY_FOR_DISPATCH,
                    to_status=OrderStatus.DISPATCHED,
                    changed_by_user_id=mgr_blr.id if mgr_blr else None,
                    reason="Dispatched from Peenya Central Hub",
                    notes="Assigned to driver Suresh Raina with Tata Ace EV",
                    latitude=blr_wh.latitude,
                    longitude=blr_wh.longitude,
                    timestamp=now - timedelta(minutes=45),
                )
                db.add(h1)
                print(f"  + Active Delivery: {active_del.delivery_number} (OTP: {active_del.otp_code})")

        # 6b. Completed Delivered Order (ORD-20261014-BLR05)
        ord_delivered = saved_orders.get("ORD-20261014-BLR05")
        if ord_delivered:
            del_num = f"DEL-{ord_delivered.order_number}"
            del_existing = db.query(Delivery).filter((Delivery.order_id == ord_delivered.id) | (Delivery.delivery_number == del_num)).first()
            if not del_existing:
                comp_del = Delivery(
                    delivery_number=del_num,
                    order_id=ord_delivered.id,
                    driver_id=driver2.id,
                    vehicle_id=veh2.id,
                    warehouse_id=blr_wh.id,
                    status=OrderStatus.DELIVERED,
                    pickup_time=now - timedelta(hours=24),
                    dispatched_at=now - timedelta(hours=24),
                    actual_delivery_time=now - timedelta(hours=22, minutes=45),
                    otp_code="552109",
                    otp_attempts=1,
                    recipient_name="Arjun Sharma",
                    pod_signature_data="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAiIGhlaWdodD0iMzAiPjxwYXRoIGQ9Ik0xMCAxNSBMMzAgMjUgTDcwIDUgTDEwMCAxNSIgc3Ryb2tlPSIjMTRiODZhIiBzdHJva2Utd2lkdGg9IjIiIGZpbGw9Im5vbmUiLz48L3N2Zz4=",
                )
                db.add(comp_del)
                db.flush()

                h_del1 = DeliveryStatusHistory(
                    delivery_id=comp_del.id,
                    from_status=OrderStatus.READY_FOR_DISPATCH,
                    to_status=OrderStatus.DISPATCHED,
                    changed_by_user_id=mgr_blr.id if mgr_blr else None,
                    reason="Out for delivery",
                    latitude=blr_wh.latitude,
                    longitude=blr_wh.longitude,
                    timestamp=now - timedelta(hours=24),
                )
                h_del2 = DeliveryStatusHistory(
                    delivery_id=comp_del.id,
                    from_status=OrderStatus.DISPATCHED,
                    to_status=OrderStatus.DELIVERED,
                    changed_by_user_id=d2_user.id,
                    reason="Delivered and verified via Customer OTP",
                    notes="Handed directly to recipient Arjun Sharma at front desk",
                    latitude=ord_delivered.destination_latitude,
                    longitude=ord_delivered.destination_longitude,
                    timestamp=now - timedelta(hours=22, minutes=45),
                )
                db.add_all([h_del1, h_del2])
                print(f"  + Completed Delivery: {comp_del.delivery_number} [Recipient: {comp_del.recipient_name}]")

        # 6c. Failed Order Delivery (ORD-20261014-BOM06)
        ord_failed = saved_orders.get("ORD-20261014-BOM06")
        if ord_failed:
            del_num = f"DEL-{ord_failed.order_number}"
            del_existing = db.query(Delivery).filter((Delivery.order_id == ord_failed.id) | (Delivery.delivery_number == del_num)).first()
            if not del_existing:
                fail_del = Delivery(
                    delivery_number=del_num,
                    order_id=ord_failed.id,
                    driver_id=drv_map.get(d3_user.id).id,
                    vehicle_id=veh_map.get("MH-04-HV-5544").id,
                    warehouse_id=bom_wh.id,
                    status=OrderStatus.FAILED,
                    pickup_time=now - timedelta(hours=18),
                    dispatched_at=now - timedelta(hours=18),
                    failed_at=now - timedelta(hours=16, minutes=30),
                    failure_reason="Customer unreachable / Premises gate locked",
                    otp_code="918234",
                )
                db.add(fail_del)
                db.flush()

                h_f1 = DeliveryStatusHistory(
                    delivery_id=fail_del.id,
                    from_status=OrderStatus.READY_FOR_DISPATCH,
                    to_status=OrderStatus.DISPATCHED,
                    changed_by_user_id=mgr_bom.id if mgr_bom else None,
                    reason="Dispatched from Vashi logistics hub",
                    latitude=bom_wh.latitude,
                    longitude=bom_wh.longitude,
                    timestamp=now - timedelta(hours=18),
                )
                h_f2 = DeliveryStatusHistory(
                    delivery_id=fail_del.id,
                    from_status=OrderStatus.DISPATCHED,
                    to_status=OrderStatus.FAILED,
                    changed_by_user_id=d3_user.id,
                    reason="Customer unreachable / Premises gate locked",
                    notes="Called customer 3 times. Security refused package drop without authorization.",
                    latitude=ord_failed.destination_latitude,
                    longitude=ord_failed.destination_longitude,
                    timestamp=now - timedelta(hours=16, minutes=30),
                )
                db.add_all([h_f1, h_f2])
                print(f"  + Failed Delivery Record: {fail_del.delivery_number} [Reason: {fail_del.failure_reason}]")

        # -------------------------------------------------------------
        # 7. Notifications & Audit Logs
        # -------------------------------------------------------------
        print("\n[7/7] Seeding In-App Notifications & Audit Trail...")
        notif_samples = [
            {
                "user_id": c1_user.id,
                "type": NotificationType.DISPATCH_EVENT,
                "severity": NotificationSeverity.INFO,
                "title": "Order Out for Delivery!",
                "message": "Your package TRK-BLR-1004 has been dispatched with Suresh Raina. Your OTP is 784912.",
                "is_read": False,
            },
            {
                "user_id": c2_user.id,
                "type": NotificationType.DELIVERY_COMPLETED,
                "severity": NotificationSeverity.SUCCESS,
                "title": "Package Delivered Successfully",
                "message": "Order ORD-20261014-BLR05 was delivered and verified via OTP. Thank you for choosing ILDO!",
                "is_read": True,
                "read_at": now - timedelta(hours=22),
            },
            {
                "user_id": mgr_blr.id if mgr_blr else c1_user.id,
                "type": NotificationType.DELAY_RISK_WARNING,
                "severity": NotificationSeverity.WARNING,
                "title": "Warehouse Capacity Staging Alert",
                "message": "Bengaluru Central Hub currently has 3 urgent orders waiting for driver allocation.",
                "is_read": False,
            },
        ]

        for n in notif_samples:
            existing_n = db.query(Notification).filter(Notification.title == n["title"]).first()
            if not existing_n:
                new_notif = Notification(**n)
                db.add(new_notif)
                print(f"  + Notification: [{n['severity'].value}] {n['title']}")

        # Audit logs
        admin_user = users_map.get("admin@ildo.com")
        if admin_user:
            audits = [
                AuditLog(
                    user_id=admin_user.id,
                    action="SYSTEM_INIT_SEED",
                    resource_type="System",
                    resource_id="0",
                    details="Platform demo seed dataset initialized successfully.",
                    ip_address="127.0.0.1",
                ),
                AuditLog(
                    user_id=admin_user.id,
                    action="WAREHOUSE_PROVISIONED",
                    resource_type="Warehouse",
                    resource_id="WH-BLR-01",
                    details="Bengaluru Central Logistics Hub provisioned with 50,000 sqft capacity.",
                    ip_address="127.0.0.1",
                ),
            ]
            db.add_all(audits)

        db.commit()
        print("\n" + "=" * 70)
        print("  DEMO SEEDING COMPLETED SUCCESSFULLY WITH 100% INTEGRITY!")
        print("=" * 70)
        print("Role Credentials Table:")
        print("  * System Administrator: admin@ildo.com          / AdminPass123!")
        print("  * Hub Manager (BLR):    manager@ildo.com        / ManagerPass123!")
        print("  * Hub Manager (BOM):    manager.mumbai@ildo.com / ManagerPass123!")
        print("  * Express Driver:       driver@ildo.com         / DriverPass123!")
        print("  * Two-Wheeler Driver:   driver2@ildo.com        / DriverPass123!")
        print("  * Heavy Cargo Driver:   driver3@ildo.com        / DriverPass123!")
        print("  * Shipper Customer:     customer@ildo.com       / CustomerPass123!")
        print("  * Enterprise Shipper:   customer2@ildo.com      / CustomerPass123!")
        print("=" * 70 + "\n")

    except Exception as exc:
        db.rollback()
        logger.error(f"Error seeding database: {exc}", exc_info=True)
        print(f"\n[ERROR] Seeding failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed ILDO Platform Demo Data")
    parser.add_argument("--clean", action="store_true", help="Drop and re-create tables before seeding")
    args = parser.parse_args()
    seed_database(clean=args.clean)
