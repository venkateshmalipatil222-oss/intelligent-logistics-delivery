from typing import List, Optional
from backend.app.models.enums import VehicleType, DeliveryPriority
from backend.app.schemas.intelligence import (
    CostLineItem,
    CostEstimationRequest,
    CostEstimationResponse,
)


class CostEstimationEngine:
    """
    Transparent Operating Cost Estimation Engine.
    Breaks down delivery costs into fuel consumption, driver labor hours,
    vehicle wear & tear depreciation, handling fees, priority surcharges, and taxes.
    """

    BASE_DISPATCH_FEE_INR = 40.0
    DRIVER_HOURLY_RATE_INR = 130.0
    MAINTENANCE_PER_KM_INR = 3.20
    GST_RATE = 0.18  # 18% GST on freight services

    # Default energy rates
    DIESEL_PRICE_PER_LITER = 92.50
    PETROL_PRICE_PER_LITER = 101.20
    ELECTRIC_PRICE_PER_KWH = 8.80

    @classmethod
    def calculate_cost(cls, request: CostEstimationRequest) -> CostEstimationResponse:
        """
        Calculates itemized cost breakdown for a delivery shipment.
        """
        dist_km = request.distance_km
        weight_kg = request.package_weight_kg
        line_items: List[CostLineItem] = []

        # 1. Base Dispatch & Handling
        line_items.append(
            CostLineItem(
                category="BASE",
                label="Base Dispatch & Terminal Handling",
                rate_basis="Fixed platform dispatch fee",
                quantity=1.0,
                unit="dispatch",
                unit_cost_inr=cls.BASE_DISPATCH_FEE_INR,
                total_inr=cls.BASE_DISPATCH_FEE_INR,
            )
        )

        # 2. Fuel / Energy Expense
        if request.vehicle_type == VehicleType.ELECTRIC_VAN:
            eff = request.fuel_efficiency_kmpl or 16.0  # km per kWh
            energy_used = dist_km / max(1.0, eff)
            fuel_cost = round(energy_used * cls.ELECTRIC_PRICE_PER_KWH, 2)
            fuel_label = "Electricity (EV Charging)"
            fuel_unit = "kWh"
            fuel_unit_price = cls.ELECTRIC_PRICE_PER_KWH
            fuel_qty = round(energy_used, 2)
        elif request.vehicle_type == VehicleType.BIKE:
            eff = request.fuel_efficiency_kmpl or 38.0  # km per L
            fuel_used = dist_km / max(1.0, eff)
            fuel_cost = round(fuel_used * cls.PETROL_PRICE_PER_LITER, 2)
            fuel_label = "Fuel (Petrol 2-Wheeler)"
            fuel_unit = "Liters"
            fuel_unit_price = cls.PETROL_PRICE_PER_LITER
            fuel_qty = round(fuel_used, 2)
        elif request.vehicle_type == VehicleType.TRUCK:
            eff = request.fuel_efficiency_kmpl or 7.5  # km per L
            fuel_used = dist_km / max(1.0, eff)
            fuel_cost = round(fuel_used * cls.DIESEL_PRICE_PER_LITER, 2)
            fuel_label = "Commercial Diesel (Medium Truck)"
            fuel_unit = "Liters"
            fuel_unit_price = cls.DIESEL_PRICE_PER_LITER
            fuel_qty = round(fuel_used, 2)
        else:  # Standard VAN
            eff = request.fuel_efficiency_kmpl or 12.0  # km per L
            fuel_used = dist_km / max(1.0, eff)
            fuel_cost = round(fuel_used * cls.DIESEL_PRICE_PER_LITER, 2)
            fuel_label = "Commercial Diesel (Delivery Van)"
            fuel_unit = "Liters"
            fuel_unit_price = cls.DIESEL_PRICE_PER_LITER
            fuel_qty = round(fuel_used, 2)

        line_items.append(
            CostLineItem(
                category="FUEL",
                label=fuel_label,
                rate_basis=f"{eff} km/{fuel_unit[:-1]} @ ₹{fuel_unit_price}/{fuel_unit[:-1]}",
                quantity=fuel_qty,
                unit=fuel_unit,
                unit_cost_inr=fuel_unit_price,
                total_inr=fuel_cost,
            )
        )

        # 3. Driver Labor Cost
        # Travel duration approx 30 km/h + 15 min handling
        travel_hours = (dist_km / 30.0) + (15.0 / 60.0)
        driver_cost = round(travel_hours * cls.DRIVER_HOURLY_RATE_INR, 2)
        line_items.append(
            CostLineItem(
                category="LABOR",
                label="Driver & Courier Operational Labor",
                rate_basis=f"₹{cls.DRIVER_HOURLY_RATE_INR}/hour based on travel + delivery time",
                quantity=round(travel_hours, 2),
                unit="hours",
                unit_cost_inr=cls.DRIVER_HOURLY_RATE_INR,
                total_inr=driver_cost,
            )
        )

        # 4. Vehicle Wear & Fleet Maintenance
        maint_cost = round(dist_km * cls.MAINTENANCE_PER_KM_INR, 2)
        line_items.append(
            CostLineItem(
                category="MAINTENANCE",
                label="Vehicle Wear & Fleet Depreciation",
                rate_basis="Depreciation, tire wear, and routine servicing allowance",
                quantity=dist_km,
                unit="km",
                unit_cost_inr=cls.MAINTENANCE_PER_KM_INR,
                total_inr=maint_cost,
            )
        )

        # 5. Heavy Weight Surcharge (if > 15 kg)
        if weight_kg > 15.0:
            excess_kg = weight_kg - 15.0
            weight_cost = round(excess_kg * 4.50, 2)
            line_items.append(
                CostLineItem(
                    category="WEIGHT_SURCHARGE",
                    label="Heavy Package Handling Fee",
                    rate_basis="Excess weight over 15kg threshold @ ₹4.50/kg",
                    quantity=round(excess_kg, 1),
                    unit="kg",
                    unit_cost_inr=4.50,
                    total_inr=weight_cost,
                )
            )

        # 6. Cold Storage Handling
        cold_storage_cost = 0.0
        if request.requires_cold_storage:
            cold_storage_cost = round(65.0 + (weight_kg * 2.0), 2)
            line_items.append(
                CostLineItem(
                    category="COLD_STORAGE",
                    label="Active Cold Chain Preservation Surcharge",
                    rate_basis="Refrigerated transit compartment energy & monitoring",
                    quantity=1.0,
                    unit="shipment",
                    unit_cost_inr=cold_storage_cost,
                    total_inr=cold_storage_cost,
                )
            )

        # 7. Priority Surcharge
        operating_subtotal = cls.BASE_DISPATCH_FEE_INR + fuel_cost + driver_cost + maint_cost
        priority_surcharge = 0.0
        if request.priority == DeliveryPriority.URGENT:
            priority_surcharge = round(operating_subtotal * 0.35, 2)
            line_items.append(
                CostLineItem(
                    category="PRIORITY",
                    label="Urgent Priority Expedited Dispatch",
                    rate_basis="+35% dedicated direct-dispatch premium",
                    quantity=1.0,
                    unit="shipment",
                    unit_cost_inr=priority_surcharge,
                    total_inr=priority_surcharge,
                )
            )
        elif request.priority == DeliveryPriority.HIGH:
            priority_surcharge = round(operating_subtotal * 0.18, 2)
            line_items.append(
                CostLineItem(
                    category="PRIORITY",
                    label="High Priority Dispatch Surcharge",
                    rate_basis="+18% priority scheduling premium",
                    quantity=1.0,
                    unit="shipment",
                    unit_cost_inr=priority_surcharge,
                    total_inr=priority_surcharge,
                )
            )

        # Totals
        subtotal = round(sum(item.total_inr for item in line_items), 2)
        gst = round(subtotal * cls.GST_RATE, 2)
        total_cost = round(subtotal + gst, 2)

        explanation = (
            f"Estimated ₹{total_cost} for {dist_km} km shipment ({weight_kg} kg via {request.vehicle_type.value}). "
            f"Subtotal ₹{subtotal} (Fuel ₹{fuel_cost}, Labor ₹{driver_cost}, Maintenance ₹{maint_cost}) + ₹{gst} (18% GST)."
        )

        return CostEstimationResponse(
            distance_km=dist_km,
            package_weight_kg=weight_kg,
            vehicle_type=request.vehicle_type.value,
            priority=request.priority.value,
            fuel_expense_inr=fuel_cost,
            driver_labor_inr=driver_cost,
            vehicle_maintenance_inr=maint_cost,
            dispatch_base_fee_inr=cls.BASE_DISPATCH_FEE_INR,
            priority_surcharge_inr=priority_surcharge,
            cold_storage_surcharge_inr=cold_storage_cost,
            subtotal_inr=subtotal,
            tax_gst_inr=gst,
            total_estimated_cost_inr=total_cost,
            line_items=line_items,
            calculation_explanation=explanation,
        )
