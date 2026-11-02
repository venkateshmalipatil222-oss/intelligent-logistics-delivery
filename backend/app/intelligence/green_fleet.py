"""
Sustainable Green Logistics & Carbon Footprint (CO2) Calculation Service (Phase 12).
Calculates vehicle emissions, fuel savings, and environmental ESG metrics.
"""

from typing import Dict, Any, List


# Standard fleet emission factors (grams of CO2 per kilometer)
EMISSION_FACTORS_G_PER_KM = {
    "EV": 0.0,            # Zero tailpipe emissions
    "PETROL": 68.0,       # 2-wheeler motorbikes
    "DIESEL": 185.0,      # Delivery cargo vans
    "HEAVY_DIESEL": 420.0 # Heavy logistics trucks
}

# Average fuel efficiency (km per liter)
AVERAGE_KM_PER_LITER = {
    "PETROL": 40.0,
    "DIESEL": 12.0,
    "HEAVY_DIESEL": 4.5
}


def calculate_green_fleet_metrics(
    vehicles: List[Dict[str, Any]],
    total_delivered_km: float = 0.0,
    fuel_price_per_liter: float = 95.0
) -> Dict[str, Any]:
    """
    Computes ESG sustainability and carbon emission metrics for the fleet.
    """
    total_vehicles = len(vehicles)
    if total_vehicles == 0:
        return {
            "total_vehicles": 0,
            "ev_vehicles": 0,
            "ev_percentage": 0.0,
            "total_distance_km": total_delivered_km,
            "co2_emissions_actual_kg": 0.0,
            "co2_emissions_prevented_kg": 0.0,
            "fuel_liters_saved": 0.0,
            "fuel_cost_saved_inr": 0.0,
            "esg_rating": "N/A",
            "fleet_status": "No active vehicles"
        }

    ev_count = sum(1 for v in vehicles if str(v.get("fuel_type", "")).upper() == "ELECTRIC" or str(v.get("fuel_type", "")).upper() == "EV")
    diesel_count = sum(1 for v in vehicles if str(v.get("fuel_type", "")).upper() == "DIESEL")
    petrol_count = sum(1 for v in vehicles if str(v.get("fuel_type", "")).upper() == "PETROL")

    ev_percentage = round((ev_count / total_vehicles) * 100.0, 1)

    # Calculate actual emissions vs hypothetical 100% diesel baseline
    ev_km = total_delivered_km * (ev_count / total_vehicles) if total_vehicles > 0 else 0.0
    diesel_km = total_delivered_km * (diesel_count / total_vehicles) if total_vehicles > 0 else 0.0
    petrol_km = total_delivered_km * (petrol_count / total_vehicles) if total_vehicles > 0 else 0.0

    actual_emissions_g = (
        (ev_km * EMISSION_FACTORS_G_PER_KM["EV"]) +
        (diesel_km * EMISSION_FACTORS_G_PER_KM["DIESEL"]) +
        (petrol_km * EMISSION_FACTORS_G_PER_KM["PETROL"])
    )
    baseline_diesel_emissions_g = total_delivered_km * EMISSION_FACTORS_G_PER_KM["DIESEL"]

    co2_saved_kg = max(0.0, round((baseline_diesel_emissions_g - actual_emissions_g) / 1000.0, 2))
    actual_co2_kg = round(actual_emissions_g / 1000.0, 2)

    # Fuel saved by EV fleet
    fuel_saved_liters = round(ev_km / AVERAGE_KM_PER_LITER["DIESEL"], 1)
    cost_saved_inr = round(fuel_saved_liters * fuel_price_per_liter, 2)

    # ESG Environmental Performance Grade
    if ev_percentage >= 50.0:
        esg_rating = "A+ (Eco-Exemplary)"
    elif ev_percentage >= 30.0:
        esg_rating = "A (Low Carbon Leader)"
    elif ev_percentage >= 15.0:
        esg_rating = "B (Transitioning Fleet)"
    else:
        esg_rating = "C (High Carbon Fleet)"

    return {
        "total_vehicles": total_vehicles,
        "ev_vehicles": ev_count,
        "diesel_vehicles": diesel_count,
        "petrol_vehicles": petrol_count,
        "ev_percentage": ev_percentage,
        "total_distance_km": round(total_delivered_km, 2),
        "co2_emissions_actual_kg": actual_co2_kg,
        "co2_emissions_prevented_kg": co2_saved_kg,
        "fuel_liters_saved": fuel_saved_liters,
        "fuel_cost_saved_inr": cost_saved_inr,
        "esg_rating": esg_rating,
        "trees_equivalent_planted": round(co2_saved_kg / 21.77, 1) # ~21.77 kg CO2 absorbed per urban tree per year
    }

