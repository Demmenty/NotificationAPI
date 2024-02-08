from django.urls import include, path
from rest_framework import routers

from api.views import (
    ClientViewSet,
    DistributionsStatsView,
    DistributionStatsView,
    DistributionViewSet,
    MessageViewSet,
)

app_name = "api"

router = routers.DefaultRouter()
router.register(r"clients", ClientViewSet)
router.register(r"distributions", DistributionViewSet)
router.register(r"messages", MessageViewSet)


urlpatterns = [
    path(
        "distributions/stats/",
        DistributionsStatsView.as_view(),
        name="distributions-stats",
    ),
    path(
        "distributions/<int:pk>/stats/",
        DistributionStatsView.as_view(),
        name="distribution-stats",
    ),
    path("", include(router.urls)),
]
