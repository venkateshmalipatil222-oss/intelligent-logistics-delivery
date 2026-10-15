from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base
from backend.app.models.enums import OrderStatus, DeliveryPriority


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_number = Column(String(50), unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="SET NULL"), nullable=True, index=True)
    destination_address = Column(String(255), nullable=False)
    destination_city = Column(String(100), nullable=False)
    destination_state = Column(String(100), nullable=False)
    destination_postal_code = Column(String(20), nullable=False)
    destination_latitude = Column(Float, nullable=False)
    destination_longitude = Column(Float, nullable=False)
    priority = Column(SAEnum(DeliveryPriority), default=DeliveryPriority.MEDIUM, nullable=False, index=True)
    status = Column(SAEnum(OrderStatus), default=OrderStatus.CREATED, nullable=False, index=True)
    estimated_distance_km = Column(Float, default=0.0, nullable=False)
    estimated_delivery_cost = Column(Float, default=0.0, nullable=False)
    promised_delivery_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    customer = relationship("Customer")
    warehouse = relationship("Warehouse", back_populates="orders")
    package = relationship("Package", back_populates="order", uselist=False, cascade="all, delete-orphan")
    delivery = relationship("Delivery", back_populates="order", uselist=False)

    def __repr__(self):
        return f"<Order id={self.id} number='{self.order_number}' status='{self.status.value}' priority='{self.priority.value}'>"
