import logging

from plyer import notification

logger = logging.getLogger(__name__)


def notify_user(title: str, message: str, app_name: str = "Amadeus") -> None:
    logger.info("Notification: %s - %s", title, message)
    try:
        notification.notify(
            title=title,
            message=message,
            app_name=app_name,
            timeout=5,
        )
    except Exception as exc:
        logger.error("Failed to trigger desktop notification: %s", exc)


if __name__ == "__main__":
    notify_user("Test Title", "This is a test notification from Amadeus.")
