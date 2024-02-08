from typing import Tuple

from django.db import models
from django.utils import timezone

from api.managers import DistributionManager


class Client(models.Model):
    id = models.AutoField(primary_key=True)
    phone_number = models.CharField(
        "Номер телефона",
        max_length=12,
        unique=True,
        help_text="Формат: 7XXXXXXXXXX (10 цифр + код страны)",
    )
    operator_code = models.CharField("Код мобильного оператора", max_length=3)
    tag = models.CharField("Тэг", max_length=255, default="")
    timezone = models.SmallIntegerField(
        "Часовой пояс",
        default=0,
        help_text=(
            "Примеры: '2' - сдвиг вперед относительно UTC на 2 часа, "
            "'-5' - сдвиг назад относительно UTC на 5 часа. "
            "По умолчанию: '0' - UTC"
        ),
    )

    def __str__(self):
        return f"Клиент №{self.id}"

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"


class Distribution(models.Model):
    objects = DistributionManager()

    id = models.AutoField(primary_key=True)
    start_datetime = models.DateTimeField(
        "Время запуска рассылки",
        default=timezone.now,
        help_text=(
            "По умолчанию: текущее время. "
            "Формат: 'YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z]', по умолчанию часовой пояс по Гринвичу. "
            "Пример: '2022-01-31 12:00:00' (можно '2022-01-31', но тогда время будет установлено на 00:00)"
        ),
    )
    end_datetime = models.DateTimeField(
        "Время окончания рассылки",
        help_text=(
            "Сообщения клиентам после этого времени не доставляются. "
            "Формат: 'YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z]', по умолчанию часовой пояс по Гринвичу. "
            "Пример: '2022-01-31 12:00:00' (можно '2022-01-31', но тогда время будет установлено на 00:00)"
        ),
    )
    message_text = models.CharField("Текст сообщения", max_length=160)
    client_filter_operator_code = models.CharField(
        "Код мобильного оператора",
        max_length=3,
        default="",
        blank=True,
        help_text="Фильтр для рассылки по коду оператора клиентов. Необязательно.",
    )
    client_filter_tag = models.CharField(
        "Тэг",
        max_length=255,
        default="",
        blank=True,
        help_text="Фильтр для рассылки по тэгу клиентов. Необязательно.",
    )

    @property
    def total_messages(self):
        return self.message_set.count()

    @property
    def sent_messages(self):
        return self.message_set.filter(status=Message.MessageStatus.SENT).count()

    def __str__(self):
        return f"Рассылка №{self.id}"

    def get_filtered_clients(self) -> models.QuerySet[Client]:
        """
        Get the filtered clients for the current distribution.

        Returns:
            QuerySet[Client]: The filtered client instances.
        """

        filtered_clients = Client.objects.all()

        if self.client_filter_operator_code:
            filtered_clients = filtered_clients.filter(
                operator_code=self.client_filter_operator_code
            )

        if self.client_filter_tag:
            filtered_clients = filtered_clients.filter(tag=self.client_filter_tag)

        return filtered_clients

    def get_or_create_messages_for_sending(
        self,
    ) -> Tuple[models.QuerySet["Message"], bool]:
        """
        Retrieves or creates messages to send for the current distribution.

        Returns:
            Tuple[QuerySet[Message], bool]: The message instances
                and a flag indicating whether new messages were created.
        """

        clients = self.get_filtered_clients()

        created_messages = Message.objects.bulk_create(
            [Message(distribution=self, client=client) for client in clients],
            ignore_conflicts=True,
        )
        messages = Message.objects.filter(distribution=self, client__in=clients)

        return messages, bool(created_messages)

    def get_stats(self) -> dict:
        """
        Returns statistics about the current distribution.

        Returns:
            dict: The statistics as a dictionary with the following keys:
                - 'distribution_id': The ID of the distribution.
                - 'total_messages': The total number of messages in the distribution.
                - 'sent_messages': The number of sent messages in the distribution.
                - 'not_sent_messages': The number of not sent messages in the distribution.
        """

        total_messages = self.total_messages
        sent_messages = self.sent_messages
        not_sent_messages = total_messages - sent_messages

        return {
            "distribution_id": self.id,
            "total_messages": total_messages,
            "sent_messages": sent_messages,
            "not_sent_messages": not_sent_messages,
        }

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"


class Message(models.Model):

    class MessageStatus(models.TextChoices):
        SENT = "SENT", "Отправлено"
        NOT_SENT = "NOT_SENT", "Не отправлено"

    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(
        "Время создания сообщения (отправки)", default=timezone.now
    )
    status = models.CharField(
        "Статус отправки",
        max_length=8,
        choices=MessageStatus.choices,
        default=MessageStatus.NOT_SENT,
    )
    distribution = models.ForeignKey(
        Distribution, verbose_name="ID рассылки", on_delete=models.CASCADE
    )
    client = models.ForeignKey(
        Client, verbose_name="ID клиента", on_delete=models.PROTECT
    )

    def __str__(self):
        return f"Сообщение №{self.id}"

    class Meta:
        unique_together = ("distribution", "client")
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
