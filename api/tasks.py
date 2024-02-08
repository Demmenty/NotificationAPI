from celery import shared_task
from celery.exceptions import MaxRetriesExceededError

from api.logs import logger
from api.services import send_daily_report_to_admins, send_message, start_distribution


@shared_task(
    autoretry_for=(Exception,), max_retries=3, default_retry_delay=60, ignore_result=True
)
def start_distribution_task(distribution_id: int) -> None:
    """
    A background task that starts a message distribution to clients.

    Args:
        distribution_id: The ID of the distribution instance to start.
    """

    try:
        start_distribution(distribution_id)

    except MaxRetriesExceededError:
        logger.error(
            f"Distribution #{distribution_id}: Distribution shifted. Too many retries."
        )
        delay = 60 * 60  # 1 hour
        start_distribution_task.apply_async(args=[distribution_id], countdown=delay)


@shared_task(
    autoretry_for=(Exception,),
    max_retries=3,
    default_retry_delay=60,
    ignore_result=True,
)
def send_message_task(message_id: int) -> None:
    """
    A background task that sends a message to a client using the external mailing API.

    Args:
        message_id: The ID of the message instance to send.
    """

    try:
        send_message(message_id)

    except MaxRetriesExceededError:
        logger.error(f"Message #{message_id}: Sending shifted. Too many retries.")
        delay = 60 * 60  # 1 hour
        send_message_task.apply_async(args=[message_id], countdown=delay)


@shared_task(
    autoretry_for=(Exception,),
    max_retries=3,
    default_retry_delay=120,
    ignore_result=True,
)
def send_daily_report_to_admins_task():
    """
    A background task that sends a daily report about previous day distributions.
    """

    try:
        send_daily_report_to_admins()
    except MaxRetriesExceededError:
        logger.error(f"Sending daily report to admins aborted. Too many retries.")
