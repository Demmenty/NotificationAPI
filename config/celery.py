import os

from celery import Celery
from celery.schedules import crontab

from config.settings import REPORT_MAIL_HOUR

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

celery_app = Celery("config")
celery_app.config_from_object("django.conf:settings", namespace="CELERY")
celery_app.autodiscover_tasks()

celery_app.conf.beat_schedule = {
    "send_daily_report_to_admins_task": {
        "task": "api.tasks.send_daily_report_to_admins_task",
        "schedule": crontab(hour=REPORT_MAIL_HOUR, minute=0),
    },
}
