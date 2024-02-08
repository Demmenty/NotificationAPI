from django.urls import path

from users.views import index, logout_user

app_name = "users"

urlpatterns = [
    path("", index, name="index"),
    path("logout/", logout_user, name="logout"),
]
