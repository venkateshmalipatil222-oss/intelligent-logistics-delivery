"""
Unit and Integration Tests for Phase 10, 11, and 12 Extensions.
Validates Geofencing boundary evaluations, Green Fleet ESG metrics, and new analytics endpoints.
"""

import pytest
from backend.app.intelligence.green_fleet import calculate_green_fleet_metrics
from backend.app.intelligence.geofence import evaluate_geofence_status, calculate_meters_distance


def test_green_fleet_metrics_calculation():
    """Validates CO2 savings, EV ratio, and ESG rating calculations."""
    vehicles = [
        {"fuel_type": "ELECTRIC"},
        {"fuel_type": "ELECTRIC"},
        {"fuel_type": "DIESEL"},
        {"fuel_type": "PETROL"},
    ]
    total_km = 200.0
    res = calculate_green_fleet_metrics(vehicles, total_km, fuel_price_per_liter=95.0)

    assert res["total_vehicles"] == 4
    assert res["ev_vehicles"] == 2
    assert res["ev_percentage"] == 50.0
    assert res["co2_emissions_prevented_kg"] > 0
    assert res["fuel_liters_saved"] > 0
    assert "A+" in res["esg_rating"]
    assert res["trees_equivalent_planted"] > 0


def test_geofence_proximity_evaluation():
    """Validates 100m geofence proximity detection and curbside alerts."""
    # Coords close together (~15 meters)
    res_inside = evaluate_geofence_status(
        driver_lat=12.9716,
        driver_lon=77.5946,
        destination_lat=12.9717,
        destination_lon=77.5947,
        geofence_radius_meters=100.0,
    )
    assert res_inside["is_inside_geofence"] is True
    assert res_inside["proximity_zone"] in ["AT_DESTINATION", "APPROACHING"]
    assert res_inside["auto_arrival_triggered"] is True
    assert "arrived at your doorstep" in res_inside["customer_alert_message"]

    # Coords far apart (>1000 meters)
    res_outside = evaluate_geofence_status(
        driver_lat=12.9716,
        driver_lon=77.5946,
        destination_lat=13.0285,
        destination_lon=77.5197,
        geofence_radius_meters=100.0,
    )
    assert res_outside["is_inside_geofence"] is False
    assert res_outside["proximity_zone"] == "EN_ROUTE"
    assert res_outside["auto_arrival_triggered"] is False

