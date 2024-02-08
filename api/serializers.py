from rest_framework.serializers import (
    HyperlinkedModelSerializer,
    IntegerField,
    Serializer,
)

from api.models import Client, Distribution, Message


class ClientSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = Client
        fields = (
            "id",
            "phone_number",
            "operator_code",
            "tag",
            "timezone",
        )


class DistributionSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = Distribution
        fields = (
            "id",
            "start_datetime",
            "end_datetime",
            "message_text",
            "client_filter_operator_code",
            "client_filter_tag",
        )


class DistributionStatsSerializer(Serializer):
    distribution_id = IntegerField()
    total_messages = IntegerField()
    sent_messages = IntegerField()
    not_sent_messages = IntegerField()


class MessageSerializer(HyperlinkedModelSerializer):
    distribution = DistributionSerializer()
    client = ClientSerializer()

    class Meta:
        model = Message
        fields = (
            "id",
            "created_at",
            "status",
            "distribution",
            "client",
        )
