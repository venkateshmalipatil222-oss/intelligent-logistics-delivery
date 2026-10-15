from datetime import datetime, timezone
from typing import Dict, Any, Optional
from backend.app.models.enums import DelayRiskCategory, OrderStatus


class DelayRiskDetector:
    """
    Real-Time Delivery Delay Risk and Bottleneck Detector.
    Evaluates slippage against promised delivery SLA, detects driver stagnation,
    and assigns structured delay severity categories.
    """

    STALE_PING_THRESHOLD_MINUTES = 12.0

    @classmethod
    def evaluate_delay_risk(
        cls,
        estimated_arrival_time: datetime,
        promised_delivery_time: Optional[datetime],
        last_ping_time: Optional[datetime] = None,
        delivery_status: OrderStatus = OrderStatus.IN_TRANSIT,
    ) -> Dict[str, Any]:
        """
        Assesses delivery delay risk and returns categorical severity and explanation.
        """
        now = datetime.now(timezone.utc)
        is_delayed = False
        variance_minutes = 0.0
        reasons = []

        # Check 1: SLA Variance against Promised Delivery Time
        if promised_delivery_time:
            # Normalize timezone if naive
            if promised_delivery_time.tzinfo is None:
                promised_delivery_time = promised_delivery_time.replace(tzinfo=timezone.utc)
            if estimated_arrival_time.tzinfo is None:
                estimated_arrival_time = estimated_arrival_time.replace(tzinfo=timezone.utc)

            diff_seconds = (estimated_arrival_time - promised_delivery_time).total_seconds()
            variance_minutes = round(diff_seconds / 60.0, 1)

            if variance_minutes > 15.0:
                risk_level = DelayRiskCategory.HIGH
                is_delayed = True
                reasons.append(f"Estimated arrival is {variance_minutes} mins past promised delivery SLA")
            elif variance_minutes > 5.0:
                risk_level = DelayRiskCategory.MEDIUM
                is_delayed = True
                reasons.append(f"Slight delivery delay trending {variance_minutes} mins behind schedule")
            elif variance_minutes > -5.0:
                risk_level = DelayRiskCategory.LOW
                reasons.append("Approaching delivery deadline with tight time margin")
            else:
                risk_level = DelayRiskCategory.NONE
                reasons.append(f"On track (ahead of schedule by {abs(variance_minutes)} mins)")
        else:
            # Default risk based on status progression
            risk_level = DelayRiskCategory.NONE
            reasons.append("Operating normally (no explicit delivery deadline specified)")

        # Check 2: Stale GPS Telemetry / Driver Stoppage
        if last_ping_time and delivery_status in [OrderStatus.IN_TRANSIT, OrderStatus.OUT_FOR_DELIVERY]:
            if last_ping_time.tzinfo is None:
                last_ping_time = last_ping_time.replace(tzinfo=timezone.utc)

            time_since_ping_mins = round((now - last_ping_time).total_seconds() / 60.0, 1)
            if time_since_ping_mins > cls.STALE_PING_THRESHOLD_MINUTES:
                if risk_level in [DelayRiskCategory.NONE, DelayRiskCategory.LOW]:
                    risk_level = DelayRiskCategory.MEDIUM
                reasons.append(f"GPS telemetry stale: no ping received for {time_since_ping_mins} mins")

        explanation = "; ".join(reasons)

        return {
            "risk_level": risk_level.value,
            "is_delayed": is_delayed,
            "variance_minutes": variance_minutes,
            "explanation": explanation,
            "evaluated_at": now.isoformat(),
        }
