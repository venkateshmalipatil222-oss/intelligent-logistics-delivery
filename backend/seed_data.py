"""
Comprehensive Demo Seeder for Intelligent Logistics & Delivery Optimization Platform (ILDO).
Seeds Users, Warehouses, Fleet Vehicles, Drivers, Orders, Packages, and Active Deliveries.
Safe and idempotent: skips entities if they already exist.
"""
import sys
import os
import random
from datetime import datetime, timedelta, timezone

# Add workspace root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal
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
from backend.app.models.enums import (
    UserRole,
    DriverStatus,
    VehicleStatus,
    VehicleType,
    OrderStatus,
    DeliveryPriority,
)


def seed_database():
    db = SessionLocal()
    try:
        print("=" * 60)
        print("SEEDING INTELLIGENT LOGISTICS PLATFORM DEMO DATA")
        print("=" * 60)

        # -------------------------------------------------------------
        # 1. Users & Customers
        # -------------------------------------------------------------
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
                print(f" -> Created User: {u['email']} [{u['role'].value}]")
            else:
                users_map[u["email"]] = existing

        # -------------------------------------------------------------
        # 2. Warehouses
        # -------------------------------------------------------------
        mgr = users_map.get("manager@ildo.com")
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
                "manager_id": mgr.id if mgr else None,
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
                "manager_id": None,
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
        ]

        wh_map = {}
        for wh in warehouses_data:
            existing = db.query(Warehouse).filter(Warehouse.code == wh["code"]).first()
            if not existing:
                new_wh = Warehouse(**wh)
                db.add(new_wh)
                db.flush()
                wh_map[wh["code"]] = new_wh
                print(f" -> Created Warehouse: {wh['name']} ({wh['code']})")
            else:
                wh_map[wh["code"]] = existing

        # -------------------------------------------------------------
        # 3. Fleet Vehicles
        # -------------------------------------------------------------
        vehicles_data = [
            {
                "registration_number": "KA-01-EV-2024",
                "model": "Tata Ace EV (Electric Van)",
                "vehicle_type": VehicleType.ELECTRIC_VAN,
                "max_weight_capacity_kg": 1000.0,
                "max_volume_capacity_m3": 5.8,
                "fuel_type": "ELECTRIC",
                "fuel_efficiency_kmpl": 16.5,
                "status": VehicleStatus.AVAILABLE,
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
        ]

        veh_map = {}
        for v in vehicles_data:
            existing = db.query(Vehicle).filter(Vehicle.registration_number == v["registration_number"]).first()
            if not existing:
                new_veh = Vehicle(**v)
                db.add(new_veh)
                db.flush()
                veh_map[v["registration_number"]] = new_veh
                print(f" -> Created Vehicle: {v['registration_number']} [{v['model']}]")
            else:
                veh_map[v["registration_number"]] = existing

        # -------------------------------------------------------------
        # 4. Drivers
        # -------------------------------------------------------------
        d1_user = users_map.get("driver@ildo.com")
        d2_user = users_map.get("driver2@ildo.com")
        v1 = veh_map.get("KA-01-EV-2024")
        v2 = veh_map.get("KA-03-BK-1122")

        drivers_data = [
            {
                "user_id": d1_user.id,
                "license_number": "DL-KA-2021-998811",
                "current_vehicle_id": v1.id if v1 else None,
                "status": DriverStatus.AVAILABLE,
                "current_latitude": 13.0285,
                "current_longitude": 77.5197,
                "rating": 4.92,
                "total_deliveries_completed": 128,
                "total_deliveries_failed": 2,
            },
            {
                "user_id": d2_user.id,
                "license_number": "DL-KA-2020-554433",
                "current_vehicle_id": v2.id if v2 else None,
                "status": DriverStatus.AVAILABLE,
                "current_latitude": 12.9738,
                "current_longitude": 77.6119,
                "rating": 4.85,
                "total_deliveries_completed": 84,
                "total_deliveries_failed": 1,
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
                print(f" -> Created Driver Profile: License {d['license_number']}")
            else:
                drv_map[d["user_id"]] = existing

        # -------------------------------------------------------------
        # 5. Orders & Packages
        # -------------------------------------------------------------
        c1_user = users_map.get("customer@ildo.com")
        c1_cust = db.query(Customer).filter(Customer.user_id == c1_user.id).first()
        blr_wh = wh_map.get("WH-BLR-01")

        orders_sample = [
            {
                "order_number": "ORD-20261015-BLR01",
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
                    "tracking_number": "TRK-IND-9021",
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
            {
                "order_number": "ORD-20261015-BLR02",
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
                    "tracking_number": "TRK-WTF-5412",
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
            {
                "order_number": "ORD-20261015-BLR03",
                "customer_id": c1_cust.id,
                "warehouse_id": blr_wh.id,
                "destination_address": "7th Block, Koramangala",
                "destination_city": "Bengaluru",
                "destination_state": "Karnataka",
                "destination_postal_code": "560095",
                "destination_latitude": 12.9352,
                "destination_longitude": 77.6245,
                "priority": DeliveryPriority.MEDIUM,
                "status": OrderStatus.PROCESSING,
                "estimated_distance_km": 18.1,
                "estimated_delivery_cost": 292.2,
                "package": {
                    "tracking_number": "TRK-KOR-7731",
                    "weight_kg": 5.0,
                    "length_cm": 30.0,
                    "width_cm": 20.0,
                    "height_cm": 12.0,
                    "volume_m3": 0.0072,
                    "category": "GENERAL_MERCHANDISE",
                    "is_fragile": False,
                    "requires_cold_storage": False,
                    "is_ready_for_dispatch": False,
                },
            },
        ]

        dispatched_order = None
        for o_data in orders_sample:
            pkg_data = o_data.pop("package")
            existing = db.query(Order).filter(Order.order_number == o_data["order_number"]).first()
            if not existing:
                new_ord = Order(**o_data)
                db.add(new_ord)
                db.flush()

                new_pkg = Package(order_id=new_ord.id, **pkg_data)
                db.add(new_pkg)
                print(f" -> Created Order: {new_ord.order_number} with Tracking {pkg_data['tracking_number']}")
                if new_ord.status == OrderStatus.DISPATCHED:
                    dispatched_order = new_ord
            else:
                if existing.status == OrderStatus.DISPATCHED:
                    dispatched_order = existing

        # -------------------------------------------------------------
        # 6. Active Delivery Dispatch with OTP & History
        # -------------------------------------------------------------
        if dispatched_order:
            existing_del = db.query(Delivery).filter(Delivery.order_id == dispatched_order.id).first()
            if not existing_del:
                now = datetime.now(timezone.utc)
                driver_obj = drv_map.get(d1_user.id)
                veh_obj = veh_map.get("KA-01-EV-2024")

                demo_delivery = Delivery(
                    delivery_number="DEL-20261015-99881",
                    order_id=dispatched_order.id,
                    driver_id=driver_obj.id,
                    vehicle_id=veh_obj.id,
                    warehouse_id=blr_wh.id,
                    status=OrderStatus.DISPATCHED,
                    pickup_time=now,
                    dispatched_at=now,
                    otp_code="784912",
                )
                db.add(demo_delivery)
                db.flush()

                # History
                h1 = DeliveryStatusHistory(
                    delivery_id=demo_delivery.id,
                    from_status=None,
                    to_status=OrderStatus.DISPATCHED,
                    changed_by_user_id=mgr.id if mgr else None,
                    reason="Initial dispatch from Peenya Central Hub",
                    notes="Assigned to Suresh Raina on Tata Ace EV",
                    latitude=blr_wh.latitude,
                    longitude=blr_wh.longitude,
                    timestamp=now,
                )
                db.add(h1)

                driver_obj.status = DriverStatus.BUSY
                driver_obj.active_deliveries_count = 1
                veh_obj.status = VehicleStatus.IN_SERVICE
                print(f" -> Dispatched Demo Delivery: {demo_delivery.delivery_number} (OTP: {demo_delivery.otp_code})")

        db.commit()
        print("=" * 60)
        print("DEMO SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("Demo Credentials:")
        print("  Admin:     admin@ildo.com     / AdminPass123!")
        print("  Manager:   manager@ildo.com   / ManagerPass123!")
        print("  Driver:    driver@ildo.com    / DriverPass123!")
        print("  Customer:  customer@ildo.com  / CustomerPass123!")
        print("=" * 60)

    except Exception as exc:
        db.rollback()
        logger.error(f"Error seeding database: {exc}", exc_info=True)
        print(f"Error during seeding: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
