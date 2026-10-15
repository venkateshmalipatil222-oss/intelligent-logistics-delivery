import json
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db, SessionLocal
from backend.app.core.logger import logger
from backend.app.core.security import decode_access_token
from backend.app.models.delivery import Delivery
from backend.app.models.order import Order
from backend.app.models.driver import Driver
from backend.app.models.warehouse import Warehouse
from backend.app.models.user import User
from backend.app.models.enums import OrderStatus, UserRole
from backend.app.schemas.tracking import (
    DriverGPSPing,
    LiveTrackingState,
    LiveCoordinate,
)
from backend.app.intelligence.eta import DynamicETACalculator
from backend.app.intelligence.delay import DelayRiskDetector
from backend.app.websockets.manager import ws_manager
from backend.app.api.deps import get_current_user, get_current_driver

router = APIRouter()


def build_live_tracking_state(delivery: Delivery, db: Session) -> dict:
    """
    Constructs a comprehensive real-time tracking state packet including
    current coordinates, dynamic ETA, and delay risk assessment.
    """
    driver = delivery.driver
    order = delivery.order
    warehouse = delivery.warehouse
    vehicle = delivery.vehicle

    now = datetime.now(timezone.utc)

    # Resolve driver coordinates (or fallback to warehouse if driver hasn't pinged yet)
    drv_lat = driver.current_latitude if driver.current_latitude is not None else warehouse.latitude
    drv_lon = driver.current_longitude if driver.current_longitude is not None else warehouse.longitude

    # Compute dynamic ETA
    eta_result = DynamicETACalculator.calculate_eta(
        current_lat=drv_lat,
        current_lon=drv_lon,
        dest_lat=order.destination_latitude,
        dest_lon=order.destination_longitude,
        current_speed_kmph=0.0,
        departure_time=now,
    )

    # Compute delay risk
    delay_result = DelayRiskDetector.evaluate_delay_risk(
        estimated_arrival_time=eta_result["estimated_arrival_time"],
        promised_delivery_time=order.promised_delivery_time,
        last_ping_time=driver.last_location_updated_at,
        delivery_status=delivery.status,
    )

    # Telemetry staleness
    last_ping_seconds_ago = None
    is_stale = False
    if driver.last_location_updated_at:
        dt_ping = driver.last_location_updated_at
        if dt_ping.tzinfo is None:
            dt_ping = dt_ping.replace(tzinfo=timezone.utc)
        last_ping_seconds_ago = round((now - dt_ping).total_seconds(), 1)
        if last_ping_seconds_ago > 600.0:  # > 10 minutes
            is_stale = True
    elif delivery.status in [OrderStatus.IN_TRANSIT, OrderStatus.OUT_FOR_DELIVERY]:
        is_stale = True

    return {
        "delivery_id": delivery.id,
        "delivery_number": delivery.delivery_number,
        "order_id": order.id,
        "order_number": order.order_number,
        "status": delivery.status.value,
        "driver_id": driver.id,
        "driver_name": driver.user.full_name if driver.user else "Fleet Courier",
        "driver_phone": driver.user.phone if driver.user else None,
        "driver_rating": driver.rating,
        "vehicle_registration": vehicle.registration_number if vehicle else None,
        "vehicle_type": vehicle.vehicle_type.value if vehicle else None,
        "origin_warehouse": {
            "name": warehouse.name,
            "latitude": warehouse.latitude,
            "longitude": warehouse.longitude,
        },
        "destination": {
            "name": f"{order.destination_city} ({order.destination_address})",
            "latitude": order.destination_latitude,
            "longitude": order.destination_longitude,
        },
        "current_driver_location": {
            "name": "Live Driver Location",
            "latitude": drv_lat,
            "longitude": drv_lon,
        },
        "remaining_distance_km": eta_result["remaining_distance_km"],
        "estimated_arrival_time": eta_result["estimated_arrival_time"].isoformat(),
        "uncertainty_buffer_minutes": eta_result["uncertainty_buffer_minutes"],
        "confidence_lower_bound": eta_result["confidence_lower_bound"].isoformat(),
        "confidence_upper_bound": eta_result["confidence_upper_bound"].isoformat(),
        "traffic_condition": eta_result["traffic_condition"],
        "delay_risk_level": delay_result["risk_level"],
        "delay_explanation": delay_result["explanation"],
        "is_delayed": delay_result["is_delayed"],
        "last_ping_seconds_ago": last_ping_seconds_ago,
        "is_telemetry_stale": is_stale,
        "otp_required": delivery.status == OrderStatus.OUT_FOR_DELIVERY,
        "connection_mode": "REST_SNAPSHOT",
        "timestamp": now.isoformat(),
    }


@router.get(
    "/{delivery_id}/live",
    response_model=LiveTrackingState,
    summary="Get live tracking telemetry snapshot (REST Fallback)",
)
def get_live_tracking_snapshot(
    delivery_id: int,
    db: Session = Depends(get_db),
):
    """
    Returns full real-time telemetry snapshot for a delivery.
    Used for initial map render and automatic fallback when WebSockets are unavailable.
    """
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery ID {delivery_id} not found",
        )

    state = build_live_tracking_state(delivery, db)
    return state


@router.post(
    "/{delivery_id}/ping",
    summary="Driver pushes GPS coordinates and broadcasts to room",
)
async def push_driver_gps_ping(
    delivery_id: int,
    ping: DriverGPSPing,
    current_user: User = Depends(get_current_driver),
    db: Session = Depends(get_db),
):
    """
    Driver submits live GPS coordinates via REST:
    1. Updates driver and vehicle current coordinates and timestamp.
    2. Recalculates dynamic ETA and delay risk.
    3. Broadcasts real-time state update to all active WebSocket listeners in the delivery room.
    """
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery ID {delivery_id} not found",
        )

    driver = delivery.driver
    now = datetime.now(timezone.utc)

    driver.current_latitude = ping.latitude
    driver.current_longitude = ping.longitude
    driver.last_location_updated_at = now

    if delivery.vehicle:
        delivery.vehicle.current_latitude = ping.latitude
        delivery.vehicle.current_longitude = ping.longitude

    db.commit()

    # Build updated state packet and broadcast to room
    state = build_live_tracking_state(delivery, db)
    state["connection_mode"] = "WEBSOCKET_BROADCAST"
    await ws_manager.broadcast_to_delivery(delivery.id, state)

    return {
        "status": "success",
        "delivery_id": delivery.id,
        "latitude": ping.latitude,
        "longitude": ping.longitude,
        "remaining_distance_km": state["remaining_distance_km"],
        "estimated_arrival_time": state["estimated_arrival_time"],
        "delay_risk_level": state["delay_risk_level"],
    }


# ============================================================================
# WebSockets Endpoints
# ============================================================================
@router.websocket("/ws/{delivery_id}")
async def websocket_tracking_stream(
    websocket: WebSocket,
    delivery_id: int,
    db: Session = Depends(get_db),
):
    """
    WebSocket endpoint for real-time live map tracking.
    Clients subscribe to receive continuous driver GPS updates, dynamic ETA, and delay alerts.
    """
    try:
        delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
        if not delivery:
            await websocket.close(code=4004, reason="Delivery not found")
            return

        await ws_manager.connect_delivery(websocket, delivery_id)

        # Send initial snapshot immediately so frontend map renders without delay
        initial_state = build_live_tracking_state(delivery, db)
        initial_state["connection_mode"] = "WEBSOCKET_LIVE"
        await websocket.send_text(json.dumps(initial_state))

        # Keep socket open and process any incoming heartbeats/pings from client
        while True:
            data = await websocket.receive_text()
            # Client can send {"action": "ping"} to keep connection alive
            if data:
                try:
                    parsed = json.loads(data)
                    if parsed.get("action") == "ping":
                        await websocket.send_text(json.dumps({"action": "pong", "time": datetime.now(timezone.utc).isoformat()}))
                except Exception:
                    pass

    except WebSocketDisconnect:
        await ws_manager.disconnect_delivery(websocket, delivery_id)
    except Exception as exc:
        logger.error(f"WebSocket error in delivery room {delivery_id}: {exc}")
        await ws_manager.disconnect_delivery(websocket, delivery_id)


@router.websocket("/ws/driver/broadcast")
async def websocket_driver_broadcaster(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Authenticated WebSocket endpoint for drivers streaming high-frequency GPS coordinates.
    """
    if not token:
        await websocket.close(code=4001, reason="Authentication token required")
        return

    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        await websocket.close(code=4001, reason="Invalid authentication token")
        return

    try:
        driver = db.query(Driver).filter(Driver.user_id == user_id).first()
        if not driver:
            await websocket.close(code=4003, reason="Driver profile not found")
            return

        await ws_manager.connect_driver(websocket, driver.id)

        while True:
            text = await websocket.receive_text()
            try:
                data = json.loads(text)
                lat = float(data.get("latitude"))
                lon = float(data.get("longitude"))
                now = datetime.now(timezone.utc)

                driver.current_latitude = lat
                driver.current_longitude = lon
                driver.last_location_updated_at = now

                if driver.current_vehicle:
                    driver.current_vehicle.current_latitude = lat
                    driver.current_vehicle.current_longitude = lon

                db.commit()

                # Find any active delivery for this driver and broadcast
                active_del = (
                    db.query(Delivery)
                    .filter(
                        Delivery.driver_id == driver.id,
                        Delivery.status.in_([OrderStatus.DISPATCHED, OrderStatus.IN_TRANSIT, OrderStatus.OUT_FOR_DELIVERY]),
                    )
                    .first()
                )
                if active_del:
                    state = build_live_tracking_state(active_del, db)
                    state["connection_mode"] = "WEBSOCKET_BROADCAST"
                    await ws_manager.broadcast_to_delivery(active_del.id, state)

                # Acknowledge ping
                await websocket.send_text(json.dumps({"status": "acknowledged", "timestamp": now.isoformat()}))

            except Exception as e:
                logger.warning(f"Error handling driver GPS stream: {e}")

    except WebSocketDisconnect:
        await ws_manager.disconnect_driver(driver.id)
    except Exception as exc:
        logger.error(f"Broadcaster error: {exc}")
        if driver:
            await ws_manager.disconnect_driver(driver.id)
