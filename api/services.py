from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils import timezone

from api.logs import logger
from api.models import Distribution, Message
from api.utils import generate_stats_message
from config.settings import DEFAULT_FROM_EMAIL
from external.mailing_service import MailingServiceClient

mailing_service = MailingServiceClient()


def start_distribution(distribution_id: int) -> None:
    """
    Starts the message distribution process.

    Args:
        distribution_id (int): The ID of the distribution to start.
    """

    from .tasks import send_message_task

    try:
        distribution = Distribution.objects.get(id=distribution_id)
    except Distribution.DoesNotExist:
        logger.error(
            f"Distribution #{distribution_id}: Sending aborted. Distribution does not exist."
        )
        return

    messages, created = distribution.get_or_create_messages_for_sending()
    if messages:
        logger.info(
            f"Distribution #{distribution_id}: Start sending {len(messages)} messages..."
        )
    else:
        logger.info(f"Distribution #{distribution_id}: No messages to send.")

    for message in messages:
        send_message_task.apply_async(args=[message.id], countdown=0)


def send_message(message_id: int) -> None:
    """
    Sends a message to the client.
    Updates the message status accordingly.

    Args:
        message_id (int): The ID of the message in the database.
    """

    try:
        message = Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        logger.error(f"Message #{message_id}: Sending aborted. Message does not exist.")
        return

    if timezone.now() > message.distribution.end_datetime:
        logger.error(
            f"Message #{message_id}: Sending aborted. Distribution has already ended."
        )
        return

    if message.status == Message.MessageStatus.SENT:
        return

    mailing_service.send_message(
        text=message.distribution.message_text,
        phone_number=message.client.phone_number,
        message_id=message.id,
    )

    message.status = Message.MessageStatus.SENT
    message.save()

    logger.info(
        f"Message #{message_id}: Sent successfully to the Client #{message.client.id}."
    )


def send_daily_report_to_admins() -> None:
    """
    Sends a daily report about previous day distributions to the admins (superusers).
    """

    logger.info("Sending daily report to admins...")

    admin_emails = User.objects.filter(is_superuser=True).values_list("email", flat=True)

    if not admin_emails:
        logger.info("No admins found to send daily report.")
        return

    previous_day_distributions = Distribution.objects.get_by_previous_day()

    stats = [distribution.get_stats() for distribution in previous_day_distributions]

    message = generate_stats_message(stats)

    send_mail(
        subject="Daily distribution report",
        message=message,
        from_email=DEFAULT_FROM_EMAIL,
        recipient_list=admin_emails,
    )

    logger.info(f"Daily report sent to admins ({len(admin_emails)}).")
