# Generated by Django 4.2.10 on 2024-02-08 13:55

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Client",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "phone_number",
                    models.CharField(
                        help_text="Формат: 7XXXXXXXXXX (10 цифр + код страны)",
                        max_length=12,
                        unique=True,
                        verbose_name="Номер телефона",
                    ),
                ),
                (
                    "operator_code",
                    models.CharField(
                        max_length=3, verbose_name="Код мобильного оператора"
                    ),
                ),
                (
                    "tag",
                    models.CharField(default="", max_length=255, verbose_name="Тэг"),
                ),
                (
                    "timezone",
                    models.SmallIntegerField(
                        default=0,
                        help_text="Примеры: '2' - сдвиг вперед относительно UTC на 2 часа, '-5' - сдвиг назад относительно UTC на 5 часа. По умолчанию: '0' - UTC",
                        verbose_name="Часовой пояс",
                    ),
                ),
            ],
            options={
                "verbose_name": "Клиент",
                "verbose_name_plural": "Клиенты",
            },
        ),
        migrations.CreateModel(
            name="Distribution",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "start_datetime",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        help_text="По умолчанию: текущее время. Формат: 'YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z]', по умолчанию часовой пояс по Гринвичу. Пример: '2022-01-31 12:00:00' (можно '2022-01-31', но тогда время будет установлено на 00:00)",
                        verbose_name="Время запуска рассылки",
                    ),
                ),
                (
                    "end_datetime",
                    models.DateTimeField(
                        help_text="Сообщения клиентам после этого времени не доставляются. Формат: 'YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z]', по умолчанию часовой пояс по Гринвичу. Пример: '2022-01-31 12:00:00' (можно '2022-01-31', но тогда время будет установлено на 00:00)",
                        verbose_name="Время окончания рассылки",
                    ),
                ),
                (
                    "message_text",
                    models.CharField(max_length=160, verbose_name="Текст сообщения"),
                ),
                (
                    "client_filter_operator_code",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Фильтр для рассылки по коду оператора клиентов. Необязательно.",
                        max_length=3,
                        verbose_name="Код мобильного оператора",
                    ),
                ),
                (
                    "client_filter_tag",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Фильтр для рассылки по тэгу клиентов. Необязательно.",
                        max_length=255,
                        verbose_name="Тэг",
                    ),
                ),
            ],
            options={
                "verbose_name": "Рассылка",
                "verbose_name_plural": "Рассылки",
            },
        ),
        migrations.CreateModel(
            name="Message",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "created_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        verbose_name="Время создания сообщения (отправки)",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("SENT", "Отправлено"), ("NOT_SENT", "Не отправлено")],
                        default="NOT_SENT",
                        max_length=8,
                        verbose_name="Статус отправки",
                    ),
                ),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="api.client",
                        verbose_name="ID клиента",
                    ),
                ),
                (
                    "distribution",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="api.distribution",
                        verbose_name="ID рассылки",
                    ),
                ),
            ],
            options={
                "verbose_name": "Сообщение",
                "verbose_name_plural": "Сообщения",
                "unique_together": {("distribution", "client")},
            },
        ),
    ]
