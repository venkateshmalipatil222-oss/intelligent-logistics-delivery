from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base
from backend.app.models.enums import OrderStatus


class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    delivery_number = Column(String(50), unique=True, index=True, nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="RESTRICT"), unique=True, nullable=False, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id", ondelete="RESTRICT"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    status = Column(SAEnum(OrderStatus), default=OrderStatus.DISPATCHED, nullable=False, index=True)
    pickup_time = Column(DateTime(timezone=True), nullable=True)
    dispatched_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    actual_delivery_time = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    failure_reason = Column(String(255), nullable=True)
    route_id = Column(Integer, nullable=True)
    otp_code = Column(String(10), nullable=True)  # 6-digit OTP for completion verification
    otp_expires_at = Column(DateTime(timezone=True), nullable=True)
    otp_attempts = Column(Integer, default=0, nullable=False)
    pod_photo_url = Column(String(500), nullable=True)
    pod_signature_data = Column(Text, nullable=True)
    recipient_name = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    order = relationship("Order", back_populates="delivery")
    driver = relationship("Driver", back_populates="deliveries")
    vehicle = relationship("Vehicle", back_populates="deliveries")
    warehouse = relationship("Warehouse", back_populates="deliveries")
    status_history = relationship("DeliveryStatusHistory", back_populates="delivery", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Delivery id={self.id} number='{self.delivery_number}' status='{self.status.value}' driver_id={self.driver_id}>"


class DeliveryStatusHistory(Base):
    __tablename__ = "delivery_status_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    delivery_id = Column(Integer, ForeignKey("deliveries.id", ondelete="CASCADE"), nullable=False, index=True)
    from_status = Column(SAEnum(OrderStatus), nullable=True)
    to_status = Column(SAEnum(OrderStatus), nullable=False)
    changed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    delivery = relationship("Delivery", back_populates="status_history")
    changed_by = relationship("User")

    def __repr__(self):
        return f"<DeliveryStatusHistory id={self.id} del_id={self.delivery_id} {self.from_status} -> {self.to_status}>"
