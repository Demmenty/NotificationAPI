from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from api.logs import logger
from api.models import Distribution
from api.tasks import start_distribution_task


@receiver(signal=post_save, sender=Distribution)
def handle_distribution_creation(
    sender, instance: Distribution, created: bool, **kwargs
):
    """
    A function to handle the creation of a distribution:
    checks conditions for execution,
    sends messages to clients if conditions are met.

    Args:
        sender: The sender of the distribution (Distribution model).
        instance: The instance of the distribution model.
        created: A boolean indicating whether the instance was created.
        **kwargs: Additional keyword arguments.
    """

    if not created:
        return

    current_time = timezone.now()
    start_time = instance.start_datetime
    end_time = instance.end_datetime

    if start_time <= current_time <= end_time:
        start_distribution_task.apply_async(args=[instance.id], countdown=0)
        return

    if current_time <= start_time <= end_time:
        logger.info(f"Distribution #{instance.id}: Will start at {start_time}.")
        delay = (start_time - current_time).total_seconds()
        start_distribution_task.apply_async(args=[instance.id], countdown=delay)
        return

    logger.info(f"Distribution #{instance.id}: Will not be started!")
