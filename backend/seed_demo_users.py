"""
Safe Demo User Seeder.
Creates baseline users for Admin, Warehouse Manager, Driver, and Customer
for seamless evaluation and demonstration. Does not erase existing data.
"""
import sys
import os

# Add workspace root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.customer import Customer
from backend.app.models.enums import UserRole
from backend.app.core.security import get_password_hash
from backend.app.core.logger import logger


def seed_demo_accounts():
    db = SessionLocal()
    try:
        demo_accounts = [
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
        ]

        created_count = 0
        for acc in demo_accounts:
            existing = db.query(User).filter(User.email == acc["email"]).first()
            if not existing:
                new_user = User(
                    email=acc["email"],
                    hashed_password=get_password_hash(acc["password"]),
                    full_name=acc["full_name"],
                    phone=acc["phone"],
                    role=acc["role"],
                    is_active=True,
                    is_verified=True,
                )
                db.add(new_user)
                db.flush()

                if acc["role"] == UserRole.CUSTOMER:
                    cust = Customer(
                        user_id=new_user.id,
                        company_name=acc.get("company_name"),
                        address_line1=acc.get("address_line1"),
                        city=acc.get("city"),
                        state=acc.get("state"),
                        postal_code=acc.get("postal_code"),
                        country="India",
                        default_latitude=acc.get("latitude"),
                        default_longitude=acc.get("longitude"),
                    )
                    db.add(cust)

                created_count += 1
                logger.info(f"Seeded demo account: {acc['email']} [{acc['role'].value}]")

        db.commit()
        print(f"Seeding completed successfully. {created_count} new accounts added.")
    except Exception as exc:
        db.rollback()
        logger.error(f"Seeding error: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_accounts()
