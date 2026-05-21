import logging
from plyer import notification

logger = logging.getLogger(__name__)

def notify_user(title, message, app_name="Speech to Code"):
    """
    Triggers a native desktop toast notification.
    :param title: Notification title.
    :param message: Notification body message.
    :param app_name: Application name displaying in notification.
    """
    logger.info(f"Notification: {title} - {message}")
    try:
        notification.notify(
            title=title,
            message=message,
            app_name=app_name,
            timeout=5  # Display duration in seconds
        )
    except Exception as e:
        logger.error(f"Failed to trigger desktop notification: {e}")

# Quick local test runner
if __name__ == "__main__":
    notify_user("Test Title", "This is a test notification from Speech to Code.")
