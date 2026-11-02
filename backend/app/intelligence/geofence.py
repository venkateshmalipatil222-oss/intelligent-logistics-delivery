"""
Geofencing & Automated Proximity Alert Engine (Phase 11).
Monitors live driver distance from target coordinates and triggers automatic arrival events.
"""

import math
from typing import Dict, Any


def calculate_meters_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in meters using Haversine formula."""
    R = 6371000.0  # Earth radius in meters
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 1)


def evaluate_geofence_status(
    driver_lat: float,
    driver_lon: float,
    destination_lat: float,
    destination_lon: float,
    geofence_radius_meters: float = 100.0
) -> Dict[str, Any]:
    """
    Evaluates whether driver is within the delivery destination geofence.
    """
    distance_meters = calculate_meters_distance(
        driver_lat, driver_lon, destination_lat, destination_lon
    )
    is_inside = distance_meters <= geofence_radius_meters
    proximity_zone = "AT_DESTINATION" if distance_meters <= 30 else ("APPROACHING" if distance_meters <= 250 else "EN_ROUTE")

    return {
        "distance_meters": distance_meters,
        "geofence_radius_meters": geofence_radius_meters,
        "is_inside_geofence": is_inside,
        "proximity_zone": proximity_zone,
        "auto_arrival_triggered": is_inside,
        "recommended_status": "ARRIVED" if is_inside else ("OUT_FOR_DELIVERY" if distance_meters <= 1000 else "IN_TRANSIT"),
        "customer_alert_message": (
            "Your driver has arrived at your doorstep! Please provide your OTP."
            if is_inside
            else f"Your driver is {round(distance_meters)}m away and approaching your address."
        )
    }

