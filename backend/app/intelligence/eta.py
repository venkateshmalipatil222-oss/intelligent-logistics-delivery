import math
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Tuple
from backend.app.intelligence.routing import haversine_distance_km


class DynamicETACalculator:
    """
    Dynamic Estimated Time of Arrival (ETA) Calculator.
    Calculates remaining duration with empirical road circuity, time-of-day traffic index,
    and adaptive uncertainty confidence intervals.
    """

    ROAD_CIRCUITY_FACTOR = 1.28
    BASELINE_SPEED_KMPH = 28.0  # Urban transit average speed in km/h
    HANDOVER_TIME_MINS = 5.0    # Drop-off and customer handover buffer

    @classmethod
    def get_time_of_day_traffic_factor(cls, dt: datetime) -> Tuple[float, str]:
        """
        Determines traffic delay multiplier based on time-of-day in local urban hours:
        - Morning Rush (08:30 - 11:00): +35% delay
        - Evening Rush (17:30 - 20:30): +45% delay
        - Midday (11:00 - 17:30): +15% delay
        - Night / Early Morning (21:00 - 08:00): 0% delay (Free flow)
        """
        hour = dt.hour + (dt.minute / 60.0)

        if 8.5 <= hour <= 11.0:
            return 1.35, "HEAVY_MORNING_RUSH"
        elif 17.5 <= hour <= 20.5:
            return 1.45, "HEAVY_EVENING_RUSH"
        elif 11.0 < hour < 17.5:
            return 1.15, "MODERATE_DAYTIME"
        else:
            return 1.00, "FREE_FLOW"

    @classmethod
    def calculate_eta(
        cls,
        current_lat: float,
        current_lon: float,
        dest_lat: float,
        dest_lon: float,
        current_speed_kmph: float = 0.0,
        departure_time: datetime = None,
    ) -> Dict[str, Any]:
        """
        Calculates remaining distance, dynamic travel time, traffic index,
        and uncertainty confidence bounds.
        """
        now = departure_time or datetime.now(timezone.utc)
        straight_line_km = haversine_distance_km(current_lat, current_lon, dest_lat, dest_lon)
        road_distance_km = round(straight_line_km * cls.ROAD_CIRCUITY_FACTOR, 2)

        # Speed estimation: blend moving speed with baseline urban speed
        if current_speed_kmph and current_speed_kmph > 10.0:
            effective_speed = min(55.0, (0.6 * current_speed_kmph) + (0.4 * cls.BASELINE_SPEED_KMPH))
        else:
            effective_speed = cls.BASELINE_SPEED_KMPH

        traffic_factor, traffic_desc = cls.get_time_of_day_traffic_factor(now)
        transit_duration_mins = (road_distance_km / max(5.0, effective_speed)) * 60.0 * traffic_factor
        total_duration_mins = round(transit_duration_mins + cls.HANDOVER_TIME_MINS, 1)

        estimated_arrival = now + timedelta(minutes=total_duration_mins)

        # Dynamic confidence interval: ± (3 mins + 0.3 * distance_km)
        buffer_mins = round(3.0 + (road_distance_km * 0.3), 1)
        lower_bound = estimated_arrival - timedelta(minutes=buffer_mins)
        upper_bound = estimated_arrival + timedelta(minutes=buffer_mins)

        return {
            "straight_line_distance_km": straight_line_km,
            "remaining_distance_km": road_distance_km,
            "estimated_duration_minutes": total_duration_mins,
            "estimated_arrival_time": estimated_arrival,
            "confidence_lower_bound": lower_bound,
            "confidence_upper_bound": upper_bound,
            "uncertainty_buffer_minutes": buffer_mins,
            "traffic_factor": traffic_factor,
            "traffic_condition": traffic_desc,
            "effective_speed_kmph": round(effective_speed, 1),
        }
