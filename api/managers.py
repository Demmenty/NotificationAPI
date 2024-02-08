from django.db.models import Manager
from django.utils import timezone


class DistributionManager(Manager):
    def get_by_previous_day(self):
        previous_day_start = timezone.now() - timezone.timedelta(days=1)
        previous_day_end = timezone.now()

        previous_day_distributions = self.filter(
            start_datetime__gte=previous_day_start, start_datetime__lt=previous_day_end
        )

        return previous_day_distributions
