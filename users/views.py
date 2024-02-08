from django.contrib.auth import logout
from django.shortcuts import redirect


def index(request):
    return redirect("admin:index")


def logout_user(request):
    request.session.clear()
    logout(request)

    return redirect("admin:index")
