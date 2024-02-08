from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.models import Client, Distribution, Message
from api.serializers import (
    ClientSerializer,
    DistributionSerializer,
    DistributionStatsSerializer,
    MessageSerializer,
)

docs_view = get_schema_view(
    openapi.Info(
        title="Notification API",
        default_version="v1",
        description="Message distribution API management service",
    ),
    public=True,
)


class ClientViewSet(ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer


class DistributionViewSet(ModelViewSet):
    queryset = Distribution.objects.all()
    serializer_class = DistributionSerializer


class DistributionStatsView(APIView):
    def get(self, request, pk, *args, **kwargs):
        """
        Get distribution stats: total messages, sent messages, not sent messages
        """

        distribution = get_object_or_404(Distribution, pk=pk)
        stats = distribution.get_stats()
        serializer = DistributionStatsSerializer(stats)

        return Response(serializer.data)


class DistributionsStatsView(APIView):
    def get(self, request, *args, **kwargs):
        """
        Get all distribution stats: total messages, sent messages, not sent messages
        """

        distributions = Distribution.objects.all()
        stats = [distribution.get_stats() for distribution in distributions]
        serializer = DistributionStatsSerializer(stats, many=True)

        return Response(serializer.data)


class MessageViewSet(ReadOnlyModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    @action(detail=False, methods=["GET"], url_path="by-client/(?P<client_id>\\d+)")
    def get_by_client(self, request, client_id):
        """Get messages by client ID"""

        messages = Message.objects.filter(client_id=client_id)
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["GET"],
        url_path="by-distribution/(?P<distribution_id>\\d+)",
    )
    def get_by_distribution(self, request, distribution_id):
        """Get messages by distribution ID"""

        messages = Message.objects.filter(distribution_id=distribution_id)
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
