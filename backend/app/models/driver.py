from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base
from backend.app.models.enums import DriverStatus


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    license_number = Column(String(100), unique=True, index=True, nullable=False)
    current_vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="SET NULL"), unique=True, nullable=True)
    status = Column(SAEnum(DriverStatus), default=DriverStatus.AVAILABLE, nullable=False, index=True)
    current_latitude = Column(Float, nullable=True)
    current_longitude = Column(Float, nullable=True)
    last_location_updated_at = Column(DateTime(timezone=True), nullable=True)
    total_deliveries_completed = Column(Integer, default=0, nullable=False)
    total_deliveries_failed = Column(Integer, default=0, nullable=False)
    rating = Column(Float, default=5.0, nullable=False)
    active_deliveries_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User")
    current_vehicle = relationship("Vehicle", back_populates="driver")
    deliveries = relationship("Delivery", back_populates="driver")

    def __repr__(self):
        return f"<Driver id={self.id} user_id={self.user_id} status='{self.status.value}' deliveries={self.total_deliveries_completed}>"
