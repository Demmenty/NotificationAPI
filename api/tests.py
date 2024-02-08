import time
from unittest.mock import call, patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from api.logs import logger
from api.models import Client, Distribution, Message
from api.serializers import (
    ClientSerializer,
    DistributionSerializer,
    DistributionStatsSerializer,
    MessageSerializer,
)
from api.services import send_message
from api.tasks import start_distribution
from api.utils import generate_stats_message

# Models


class ClientModelTest(TestCase):
    def setUp(self):
        self.client_data = {
            "phone_number": "79123456789",
            "operator_code": "912",
            "tag": "test_tag",
            "timezone": 2,
        }

    def test_create_client(self):
        client = Client.objects.create(**self.client_data)

        self.assertEqual(client.phone_number, self.client_data["phone_number"])
        self.assertEqual(client.operator_code, self.client_data["operator_code"])
        self.assertEqual(client.tag, self.client_data["tag"])
        self.assertEqual(client.timezone, self.client_data["timezone"])

    def test_str_representation(self):
        client = Client.objects.create(**self.client_data)
        expected_str = f"Клиент №{client.id}"
        self.assertEqual(str(client), expected_str)

    def test_verbose_names(self):
        self.assertEqual(Client._meta.verbose_name, "Клиент")
        self.assertEqual(Client._meta.verbose_name_plural, "Клиенты")


class DistributionModelTestCase(TestCase):
    def setUp(self):
        self.distribution = Distribution.objects.create(
            start_datetime=timezone.now(),
            end_datetime=timezone.now() + timezone.timedelta(days=1),
            message_text="Test Message",
            client_filter_operator_code="890",
            client_filter_tag="test_tag",
        )

    def test_create_distribution(self):
        created_distribution = Distribution.objects.get(id=self.distribution.id)

        self.assertEqual(
            created_distribution.start_datetime, self.distribution.start_datetime
        )
        self.assertEqual(
            created_distribution.end_datetime, self.distribution.end_datetime
        )
        self.assertEqual(
            created_distribution.message_text, self.distribution.message_text
        )
        self.assertEqual(
            created_distribution.client_filter_operator_code,
            self.distribution.client_filter_operator_code,
        )
        self.assertEqual(
            created_distribution.client_filter_tag, self.distribution.client_filter_tag
        )

    def test_get_stats(self):
        client = Client.objects.create(
            phone_number="7890123456",
            operator_code=self.distribution.client_filter_operator_code,
            tag=self.distribution.client_filter_tag,
            timezone=5,
        )

        messages, created = self.distribution.get_or_create_messages_for_sending()

        stats = self.distribution.get_stats()

        self.assertEqual(stats["distribution_id"], self.distribution.id)
        self.assertEqual(stats["total_messages"], 1)
        self.assertEqual(stats["sent_messages"], 0)
        self.assertEqual(stats["not_sent_messages"], 1)

    def test_get_by_previous_day(self):
        distribution_1 = Distribution.objects.create(
            start_datetime=timezone.now() - timezone.timedelta(days=2),
            end_datetime=timezone.now(),
            message_text="Test Message 1",
        )

        distribution_2 = Distribution.objects.create(
            start_datetime=timezone.now() - timezone.timedelta(hours=1),
            end_datetime=timezone.now(),
            message_text="Test Message 2",
        )

        previous_day_distributions = Distribution.objects.get_by_previous_day()

        self.assertIn(self.distribution, previous_day_distributions)
        self.assertNotIn(distribution_1, previous_day_distributions)
        self.assertIn(distribution_2, previous_day_distributions)


class MessageModelTestCase(TestCase):
    def setUp(self):
        self.client = Client.objects.create(
            phone_number="79123456789",
            operator_code="912",
            tag="test_tag",
            timezone=0,
        )

        self.distribution = Distribution.objects.create(
            start_datetime=timezone.now(),
            end_datetime=timezone.now() + timezone.timedelta(days=1),
            message_text="Test message",
            client_filter_operator_code="912",
            client_filter_tag="test_tag",
        )

    def test_unique_together_constraint(self):
        message1 = Message.objects.create(
            status=Message.MessageStatus.NOT_SENT,
            distribution=self.distribution,
            client=self.client,
        )

        with self.assertRaises(Exception):
            message2 = Message.objects.create(
                status=Message.MessageStatus.NOT_SENT,
                distribution=self.distribution,
                client=self.client,
            )

    def test_str_representation(self):
        message = Message.objects.create(
            status=Message.MessageStatus.NOT_SENT,
            distribution=self.distribution,
            client=self.client,
        )

        self.assertEqual(str(message), f"Сообщение №{message.id}")


# Serializers


class ClientSerializerTestCase(TestCase):
    def setUp(self):
        self.client_data = {
            "phone_number": "79123456789",
            "operator_code": "912",
            "tag": "test_tag",
            "timezone": 0,
        }
        self.client = Client.objects.create(**self.client_data)

    def test_serialize_client(self):
        serializer = ClientSerializer(instance=self.client)

        expected_data = {
            "id": self.client.id,
            "phone_number": self.client.phone_number,
            "operator_code": self.client.operator_code,
            "tag": self.client.tag,
            "timezone": self.client.timezone,
        }
        self.assertEqual(serializer.data, expected_data)

    def test_deserialize_client_valid_data(self):
        valid_data = {
            "phone_number": "79111111111",
            "operator_code": "911",
            "tag": "new_tag",
            "timezone": 2,
        }

        serializer = ClientSerializer(data=valid_data)

        self.assertTrue(serializer.is_valid())

        self.assertEqual(serializer.validated_data, valid_data)

    def test_deserialize_client_invalid_data(self):
        invalid_data = {
            "operator_code": "789",
            "tag": "invalid_tag",
            "timezone": 3,
        }

        serializer = ClientSerializer(data=invalid_data)

        self.assertFalse(serializer.is_valid())

        self.assertIn("phone_number", serializer.errors)


class DistributionSerializerTestCase(TestCase):
    def setUp(self):
        self.distribution_data = {
            "start_datetime": timezone.now(),
            "end_datetime": timezone.now() + timezone.timedelta(days=1),
            "message_text": "Test Message",
            "client_filter_operator_code": "123",
            "client_filter_tag": "test_tag",
        }
        self.distribution = Distribution.objects.create(**self.distribution_data)

    def test_serialize_distribution(self):
        serializer = DistributionSerializer(instance=self.distribution)

        expected_data = {
            "id": self.distribution.id,
            "start_datetime": self.distribution.start_datetime.isoformat()[:-6] + "Z",
            "end_datetime": self.distribution.end_datetime.isoformat()[:-6] + "Z",
            "message_text": self.distribution.message_text,
            "client_filter_operator_code": self.distribution.client_filter_operator_code,
            "client_filter_tag": self.distribution.client_filter_tag,
        }

        self.assertEqual(serializer.data, expected_data)

    def test_deserialize_distribution_valid_data(self):
        valid_data = {
            "start_datetime": timezone.now(),
            "end_datetime": timezone.now() + timezone.timedelta(days=2),
            "message_text": "New Test Message",
            "client_filter_operator_code": "456",
            "client_filter_tag": "new_tag",
        }

        serializer = DistributionSerializer(data=valid_data)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data, valid_data)

    def test_deserialize_distribution_invalid_data(self):
        invalid_data = {
            "start_datetime": timezone.now(),
            "message_text": "Invalid Test Message",
        }

        serializer = DistributionSerializer(data=invalid_data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("end_datetime", serializer.errors)


class DistributionStatsSerializerTestCase(TestCase):
    def test_serialize_distribution_stats(self):
        data = {
            "distribution_id": 1,
            "total_messages": 10,
            "sent_messages": 8,
            "not_sent_messages": 2,
        }

        serializer = DistributionStatsSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        expected_data = {
            "distribution_id": 1,
            "total_messages": 10,
            "sent_messages": 8,
            "not_sent_messages": 2,
        }

        self.assertEqual(serializer.data, expected_data)


class MessageSerializerTestCase(TestCase):
    def setUp(self):
        self.client_data = {
            "phone_number": "1234567890",
            "operator_code": "234",
            "tag": "test_tag",
            "timezone": 0,
        }
        self.client = Client.objects.create(**self.client_data)

        self.distribution_data = {
            "start_datetime": timezone.now(),
            "end_datetime": timezone.now() + timezone.timedelta(days=1),
            "message_text": "Test Message",
            "client_filter_operator_code": "234",
            "client_filter_tag": "test_tag",
        }
        self.distribution = Distribution.objects.create(**self.distribution_data)

        self.message_data = {
            "created_at": timezone.now(),
            "status": Message.MessageStatus.SENT,
            "distribution": self.distribution,
            "client": self.client,
        }
        self.message = Message.objects.create(**self.message_data)

    def test_serialize_message(self):
        serializer = MessageSerializer(instance=self.message)

        expected_data = {
            "id": self.message.id,
            "created_at": self.message.created_at.isoformat()[:-6] + "Z",
            "status": Message.MessageStatus.SENT.value,
            "distribution": DistributionSerializer(self.message.distribution).data,
            "client": ClientSerializer(self.message.client).data,
        }

        self.assertEqual(serializer.data, expected_data)


# Views


class ClientViewSetTestCase(APITestCase):
    def setUp(self):
        self.client_data = {
            "phone_number": "1234567890",
            "operator_code": "123",
            "tag": "test_tag",
            "timezone": 0,
        }
        self.client_instance = Client.objects.create(**self.client_data)
        self.client_serializer = ClientSerializer(instance=self.client_instance)

    def test_list_clients(self):
        url = reverse("api:client-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_data = [self.client_serializer.data]
        self.assertEqual(response.data, expected_data)

    def test_retrieve_client(self):
        url = reverse("api:client-detail", kwargs={"pk": self.client_instance.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_data = self.client_serializer.data
        self.assertEqual(response.data, expected_data)

    def test_create_client(self):
        url = reverse("api:client-list")
        new_client_data = {
            "phone_number": "9876543210",
            "operator_code": "876",
            "tag": "new_test_tag",
            "timezone": 3,
        }

        response = self.client.post(url, data=new_client_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_client = Client.objects.get(phone_number=new_client_data["phone_number"])
        new_client_serializer = ClientSerializer(instance=new_client)

        self.assertEqual(response.data, new_client_serializer.data)

    def test_update_client(self):
        url = reverse("api:client-detail", kwargs={"pk": self.client_instance.id})
        updated_data = {
            "phone_number": "9999999999",
            "operator_code": "999",
            "tag": "updated_test_tag",
            "timezone": -5,
        }

        response = self.client.put(url, data=updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client_instance.refresh_from_db()
        updated_client_serializer = ClientSerializer(instance=self.client_instance)

        self.assertEqual(response.data, updated_client_serializer.data)

    def test_delete_client(self):
        url = reverse("api:client-detail", kwargs={"pk": self.client_instance.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        with self.assertRaises(Client.DoesNotExist):
            Client.objects.get(id=self.client_instance.id)


class DistributionViewSetTestCase(APITestCase):
    def setUp(self):
        self.distribution_data = {
            "start_datetime": timezone.now(),
            "end_datetime": timezone.now() + timezone.timedelta(days=1),
            "message_text": "Test Message",
            "client_filter_operator_code": "123",
            "client_filter_tag": "test_tag",
        }
        self.distribution = Distribution.objects.create(**self.distribution_data)
        self.url = reverse("api:distribution-list")

    def test_list_distributions(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_data = DistributionSerializer(instance=self.distribution).data
        self.assertIn(expected_data, response.data)

    def test_retrieve_distribution(self):
        retrieve_url = reverse(
            "api:distribution-detail", kwargs={"pk": self.distribution.id}
        )
        response = self.client.get(retrieve_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_data = DistributionSerializer(instance=self.distribution).data
        self.assertEqual(response.data, expected_data)

    def test_create_distribution(self):
        data = {
            "start_datetime": timezone.now(),
            "end_datetime": timezone.now() + timezone.timedelta(days=1),
            "message_text": "New Test Message",
            "client_filter_operator_code": "456",
            "client_filter_tag": "new_test_tag",
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created_distribution = Distribution.objects.get(id=response.data["id"])
        self.assertEqual(created_distribution.message_text, data["message_text"])

    def test_update_distribution(self):
        update_url = reverse(
            "api:distribution-detail", kwargs={"pk": self.distribution.id}
        )
        data = {
            "message_text": "Updated Test Message",
        }

        response = self.client.patch(update_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        updated_distribution = Distribution.objects.get(id=self.distribution.id)
        self.assertEqual(updated_distribution.message_text, data["message_text"])

    def test_delete_distribution(self):
        delete_url = reverse(
            "api:distribution-detail", kwargs={"pk": self.distribution.id}
        )
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        with self.assertRaises(Distribution.DoesNotExist):
            Distribution.objects.get(id=self.distribution.id)


class DistributionStatsViewTestCase(APITestCase):
    def setUp(self):
        self.distribution_data = {
            "start_datetime": timezone.now(),
            "end_datetime": timezone.now() + timezone.timedelta(days=1),
            "message_text": "Test Message",
            "client_filter_operator_code": "123",
            "client_filter_tag": "test_tag",
        }
        self.distribution = Distribution.objects.create(**self.distribution_data)
        self.url = reverse("api:distribution-stats", kwargs={"pk": self.distribution.id})

    def test_get_distribution_stats(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_stats = DistributionStatsSerializer(
            instance=self.distribution.get_stats()
        ).data
        self.assertEqual(response.data, expected_stats)

    def test_get_distribution_stats_invalid_distribution(self):
        invalid_url = reverse("api:distribution-stats", kwargs={"pk": 999})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class DistributionsStatsViewTestCase(APITestCase):
    def setUp(self):
        self.distribution_data_1 = {
            "start_datetime": timezone.now(),
            "end_datetime": timezone.now() + timezone.timedelta(days=1),
            "message_text": "Test Message 1",
            "client_filter_operator_code": "123",
            "client_filter_tag": "test_tag_1",
        }
        self.distribution_1 = Distribution.objects.create(**self.distribution_data_1)

        self.distribution_data_2 = {
            "start_datetime": timezone.now(),
            "end_datetime": timezone.now() + timezone.timedelta(days=2),
            "message_text": "Test Message 2",
            "client_filter_operator_code": "456",
            "client_filter_tag": "test_tag_2",
        }
        self.distribution_2 = Distribution.objects.create(**self.distribution_data_2)

        self.url = reverse("api:distributions-stats")

    def test_get_all_distribution_stats(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_stats = DistributionStatsSerializer(
            instance=[self.distribution_1.get_stats(), self.distribution_2.get_stats()],
            many=True,
        ).data
        self.assertEqual(response.data, expected_stats)


class MessageViewSetTestCase(APITestCase):
    def setUp(self):
        self.client_1 = Client.objects.create(
            phone_number="1234567890",
            operator_code="234",
            tag="test_tag_1",
            timezone=0,
        )

        self.distribution_1 = Distribution.objects.create(
            end_datetime=timezone.now() + timezone.timedelta(days=1),
            message_text="Test Message 1",
        )

        self.message_1 = Message.objects.create(
            status=Message.MessageStatus.SENT,
            distribution=self.distribution_1,
            client=self.client_1,
        )

        self.url_by_client = reverse(
            "api:message-get-by-client", args=[self.client_1.id]
        )
        self.url_by_distribution = reverse(
            "api:message-get-by-distribution", args=[self.distribution_1.id]
        )

    def test_get_messages_by_client(self):
        response = self.client.get(self.url_by_client)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_data = MessageSerializer(instance=[self.message_1], many=True).data
        self.assertEqual(response.data, expected_data)

    def test_get_messages_by_distribution(self):
        response = self.client.get(self.url_by_distribution)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_data = MessageSerializer(instance=[self.message_1], many=True).data
        self.assertEqual(response.data, expected_data)


# Handlers


class DistributionSignalHandlerTestCase(TestCase):
    @patch("api.tasks.start_distribution_task.apply_async")
    def test_handle_immediate_distribution_creation(self, start_distribution_task_mock):
        distribution_data = {
            "start_datetime": timezone.now(),
            "end_datetime": timezone.now() + timezone.timedelta(days=1),
            "message_text": "Test Message",
        }
        distribution = Distribution.objects.create(**distribution_data)

        time.sleep(1)

        start_distribution_task_mock.assert_called_once_with(
            args=[distribution.id],
            countdown=0,
        )

    @patch("api.tasks.start_distribution_task")
    def test_handle_deferred_distribution_creation(self, start_distribution_task_mock):
        distribution_data = {
            "start_datetime": timezone.now() + timezone.timedelta(seconds=10),
            "end_datetime": timezone.now() + timezone.timedelta(days=1),
            "message_text": "Test Message",
        }

        with self.assertLogs(logger, level="INFO") as log_output:
            distribution = Distribution.objects.create(**distribution_data)

            time.sleep(1)

            self.assertIn(
                f"INFO:{logger.name}:Distribution #{distribution.id}: Will start at {distribution.start_datetime}.",
                log_output.output,
            )

        start_distribution_task_mock.assert_not_called()

    @patch("api.tasks.start_distribution_task.apply_async")
    def test_handle_invalid_distribution_creation(self, start_distribution_task_mock):
        distribution_data = {
            "start_datetime": timezone.now(),
            "end_datetime": timezone.now() - timezone.timedelta(days=1),
            "message_text": "Test Message",
        }

        with self.assertLogs(logger, level="INFO") as log_output:
            distribution = Distribution.objects.create(**distribution_data)

            time.sleep(1)

            self.assertIn(
                f"INFO:{logger.name}:Distribution #{distribution.id}: Will not be started!",
                log_output.output,
            )

        start_distribution_task_mock.assert_not_called()


# Services


class StartDistributionTestCase(TestCase):
    def setUp(self):
        self.distribution = Distribution.objects.create(
            start_datetime=timezone.now(),
            end_datetime=timezone.now() + timezone.timedelta(days=1),
            message_text="Test Message",
        )

    @patch("api.tasks.send_message_task.apply_async")
    @patch("api.models.Distribution.get_or_create_messages_for_sending")
    def test_start_distribution_with_messages(
        self, get_or_create_mock, send_message_task_mock
    ):
        messages = [Message(id=1), Message(id=2)]
        get_or_create_mock.return_value = (messages, True)

        start_distribution(self.distribution.id)

        get_or_create_mock.assert_called_once_with()
        send_message_task_mock.assert_has_calls(
            [call(args=[1], countdown=0), call(args=[2], countdown=0)]
        )

    @patch("api.tasks.send_message_task.apply_async")
    @patch("api.models.Distribution.get_or_create_messages_for_sending")
    def test_start_distribution_no_messages(
        self, get_or_create_mock, send_message_task_mock
    ):
        get_or_create_mock.return_value = ([], False)

        start_distribution(self.distribution.id)

        get_or_create_mock.assert_called_once_with()
        send_message_task_mock.assert_not_called()

    @patch("api.tasks.send_message_task.apply_async")
    def test_start_distribution_nonexistent_distribution(self, send_message_task_mock):
        start_distribution(999)

        self.assertRaises(Distribution.DoesNotExist)
        self.assertLogs(logger, level="ERROR")
        send_message_task_mock.assert_not_called()


class SendMessageTestCase(TestCase):
    def setUp(self):
        self.client = Client.objects.create(phone_number="1234567890")
        self.distribution = Distribution.objects.create(
            start_datetime=timezone.now(),
            end_datetime=timezone.now() + timezone.timedelta(days=1),
            message_text="Test Message",
        )
        self.message = Message.objects.create(
            distribution=self.distribution,
            client=self.client,
            status=Message.MessageStatus.NOT_SENT,
        )

    @patch("api.services.mailing_service.send_message")
    def test_send_message_success(self, send_message_mock):
        send_message_mock.return_value = True

        send_message(self.message.id)

        self.message.refresh_from_db()
        self.assertEqual(self.message.status, Message.MessageStatus.SENT)
        send_message_mock.assert_called_once_with(
            text=self.distribution.message_text,
            phone_number=self.client.phone_number,
            message_id=self.message.id,
        )

    @patch("api.services.mailing_service.send_message")
    def test_send_message_does_not_exist(self, send_message_mock):
        send_message_mock.return_value = True

        send_message(999)

        send_message_mock.assert_not_called()

    @patch("api.services.mailing_service.send_message")
    def test_send_message_distribution_ended(self, send_message_mock):
        send_message_mock.return_value = True
        self.distribution.end_datetime = timezone.now() - timezone.timedelta(days=1)
        self.distribution.save()

        send_message(self.message.id)

        send_message_mock.assert_not_called()
        self.message.refresh_from_db()
        self.assertEqual(self.message.status, Message.MessageStatus.NOT_SENT)

    @patch("api.services.mailing_service.send_message")
    def test_send_message_already_sent(self, send_message_mock):
        send_message_mock.return_value = True
        self.message.status = Message.MessageStatus.SENT
        self.message.save()

        send_message(self.message.id)

        send_message_mock.assert_not_called()
        self.message.refresh_from_db()
        self.assertEqual(self.message.status, Message.MessageStatus.SENT)


# Utils


class GenerateStatsMessageTestCase(TestCase):
    def test_empty_stats(self):
        stats = []
        expected_message = (
            "Статистика по рассылкам, запущенным за предыдущий день.\n\n"
            "Всего рассылок: 0\n"
        )
        self.assertEqual(generate_stats_message(stats), expected_message)

    def test_non_empty_stats(self):
        stats = [
            {
                "distribution_id": 1,
                "total_messages": 10,
                "sent_messages": 7,
                "not_sent_messages": 3,
            },
            {
                "distribution_id": 2,
                "total_messages": 15,
                "sent_messages": 12,
                "not_sent_messages": 3,
            },
        ]
        expected_message = (
            "Статистика по рассылкам, запущенным за предыдущий день.\n\n"
            "Всего рассылок: 2\n"
            "Всего отправлено сообщений: 19\n\n"
            "Детальный список:\n"
            "- Рассылка #1: Всего сообщений: 10, Отправлено: 7, Не отправлено: 3\n"
            "- Рассылка #2: Всего сообщений: 15, Отправлено: 12, Не отправлено: 3\n"
        )
        self.assertEqual(generate_stats_message(stats), expected_message)
