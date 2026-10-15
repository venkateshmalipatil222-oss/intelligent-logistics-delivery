from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base
from backend.app.models.enums import VehicleType, VehicleStatus


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    registration_number = Column(String(50), unique=True, index=True, nullable=False)
    model = Column(String(100), nullable=False)
    vehicle_type = Column(SAEnum(VehicleType), default=VehicleType.VAN, nullable=False)
    max_weight_capacity_kg = Column(Float, nullable=False)  # Maximum payload weight in kg
    max_volume_capacity_m3 = Column(Float, nullable=False)  # Maximum payload volume in m3
    fuel_type = Column(String(50), default="DIESEL", nullable=False)
    fuel_efficiency_kmpl = Column(Float, default=12.0, nullable=False)
    status = Column(SAEnum(VehicleStatus), default=VehicleStatus.AVAILABLE, nullable=False, index=True)
    current_latitude = Column(Float, nullable=True)
    current_longitude = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    driver = relationship("Driver", back_populates="current_vehicle", uselist=False)
    deliveries = relationship("Delivery", back_populates="vehicle")

    def __repr__(self):
        return f"<Vehicle id={self.id} reg='{self.registration_number}' type='{self.vehicle_type.value}' status='{self.status.value}'>"
