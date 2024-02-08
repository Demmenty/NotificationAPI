import logging
import sys

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from api.models import Client, Distribution

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="[%(asctime)s] API: %(message)s",
    datefmt="%d/%b/%Y %H:%M:%S",
)

logger = logging.getLogger("API")


@receiver(post_save, sender=Client)
def log_client_save(sender, instance: Client, created: bool, **kwargs):
    if created:
        logger.info(f"Client #{instance.id}: Created.")
    else:
        logger.info(f"Client #{instance.id}: Updated.")


@receiver(post_delete, sender=Client)
def log_client_delete(sender, instance: Client, **kwargs):
    logger.info(f"Client #{instance.id}: Deleted.")


@receiver(post_save, sender=Distribution)
def log_distribution_save(sender, instance: Distribution, created: bool, **kwargs):
    if created:
        logger.info(f"Distribution #{instance.id}: Created.")
    else:
        logger.info(f"Distribution #{instance.id}: Updated.")


@receiver(post_delete, sender=Distribution)
def log_distribution_delete(sender, instance: Distribution, **kwargs):
    logger.info(f"Distribution #{instance.id}: Deleted.")
