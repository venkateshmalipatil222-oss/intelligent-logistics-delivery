import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.notification import Notification
from backend.app.models.enums import NotificationType, NotificationSeverity
from backend.app.core.logger import logger


def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    type: NotificationType = NotificationType.SYSTEM_ALERT,
    severity: NotificationSeverity = NotificationSeverity.INFO,
    delivery_id: Optional[int] = None,
    order_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Notification:
    """
    Persist an in-app notification record for a user.
    """
    metadata_json = json.dumps(metadata) if metadata else None
    notification = Notification(
        user_id=user_id,
        delivery_id=delivery_id,
        order_id=order_id,
        type=type,
        severity=severity,
        title=title,
        message=message,
        metadata_json=metadata_json,
    )
    db.add(notification)
    db.flush()
    logger.info(f"Notification created for User #{user_id}: [{severity.value}] {title}")
    return notification


def notify_delivery_dispatched(db: Session, delivery, customer_user_id: Optional[int] = None):
    """Notify customer and driver that order has been dispatched."""
    if customer_user_id:
        create_notification(
            db=db,
            user_id=customer_user_id,
            title=f"Order Dispatched ({delivery.delivery_number})",
            message=f"Your delivery #{delivery.delivery_number} has been dispatched. Track in real time on your dashboard.",
            type=NotificationType.DISPATCH_EVENT,
            severity=NotificationSeverity.INFO,
            delivery_id=delivery.id,
            order_id=delivery.order_id,
            metadata={"otp_code": delivery.otp_code},
        )


def notify_delivery_completed(db: Session, delivery, customer_user_id: Optional[int] = None):
    """Notify customer and managers that delivery is successfully completed."""
    if customer_user_id:
        create_notification(
            db=db,
            user_id=customer_user_id,
            title="Package Delivered Successfully",
            message=f"Delivery #{delivery.delivery_number} was successfully verified with OTP and handed over.",
            type=NotificationType.DELIVERY_COMPLETED,
            severity=NotificationSeverity.SUCCESS,
            delivery_id=delivery.id,
            order_id=delivery.order_id,
        )


def notify_delivery_failed(
    db: Session,
    delivery,
    reason: str,
    notes: str,
    customer_user_id: Optional[int] = None,
):
    """Notify customer and managers regarding delivery attempt failure."""
    if customer_user_id:
        create_notification(
            db=db,
            user_id=customer_user_id,
            title="Delivery Attempt Failed",
            message=f"Delivery #{delivery.delivery_number} could not be completed. Reason: {reason}. Remarks: {notes}",
            type=NotificationType.DELIVERY_FAILED,
            severity=NotificationSeverity.CRITICAL,
            delivery_id=delivery.id,
            order_id=delivery.order_id,
            metadata={"reason": reason, "notes": notes},
        )


def notify_otp_regenerated(db: Session, delivery, customer_user_id: int, new_otp: str):
    """Notify customer of newly refreshed security OTP."""
    create_notification(
        db=db,
        user_id=customer_user_id,
        title="New Delivery Security OTP",
        message=f"A fresh security verification OTP for delivery #{delivery.delivery_number} has been generated: {new_otp}. Valid for 60 minutes.",
        type=NotificationType.OTP_GENERATED,
        severity=NotificationSeverity.WARNING,
        delivery_id=delivery.id,
        order_id=delivery.order_id,
        metadata={"new_otp": new_otp},
    )
