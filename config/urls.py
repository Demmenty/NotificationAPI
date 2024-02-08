from django.contrib import admin
from django.urls import include, path

from api.views import docs_view

urlpatterns = [
    path("", include("users.urls", namespace="users")),
    path("social/", include("social_django.urls", namespace="social")),
    path("api/", include("api.urls", namespace="api")),
    path(
        "docs/", docs_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"
    ),
    path("admin/", admin.site.urls),
]
