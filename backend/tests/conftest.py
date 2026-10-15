import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.main import app
from backend.app.core.database import Base, get_db

# Create an isolated in-memory SQLite database strictly for testing (Rule 30)
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all tables in test database once for session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    """Provides a fresh transactional database session per test with automatic rollback."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """Provides an isolated TestClient with dependency overrides."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


from backend.app.models.user import User
from backend.app.models.customer import Customer
from backend.app.models.enums import UserRole
from backend.app.core.security import get_password_hash, create_access_token


@pytest.fixture
def auth_tokens(db_session):
    """Creates test users across all roles and returns authentication headers."""
    admin = User(
        email="test_admin@ildo.com",
        hashed_password=get_password_hash("AdminPass123!"),
        full_name="Test Admin",
        role=UserRole.ADMIN,
        is_active=True,
    )
    manager = User(
        email="test_manager@ildo.com",
        hashed_password=get_password_hash("ManagerPass123!"),
        full_name="Test Manager",
        role=UserRole.WAREHOUSE_MANAGER,
        is_active=True,
    )
    driver_user = User(
        email="test_driver@ildo.com",
        hashed_password=get_password_hash("DriverPass123!"),
        full_name="Test Driver",
        role=UserRole.DRIVER,
        is_active=True,
    )
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
