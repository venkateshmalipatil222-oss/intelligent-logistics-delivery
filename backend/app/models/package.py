from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base


class Package(Base):
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    tracking_number = Column(String(60), unique=True, index=True, nullable=False)
    weight_kg = Column(Float, nullable=False)  # Weight in kilograms
    length_cm = Column(Float, default=20.0, nullable=False)
    width_cm = Column(Float, default=15.0, nullable=False)
    height_cm = Column(Float, default=10.0, nullable=False)
    volume_m3 = Column(Float, default=0.003, nullable=False)  # Volume in cubic meters
    category = Column(String(100), default="GENERAL", nullable=False)
    is_fragile = Column(Boolean, default=False, nullable=False)
    requires_cold_storage = Column(Boolean, default=False, nullable=False)
    is_ready_for_dispatch = Column(Boolean, default=False, nullable=False)
    prepared_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    order = relationship("Order", back_populates="package")

    def __repr__(self):
        return f"<Package id={self.id} tracking='{self.tracking_number}' weight={self.weight_kg}kg ready={self.is_ready_for_dispatch}>"
