from django.contrib.auth.models import User
from rest_framework.test import APITestCase


class IndexViewTestCase(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin", password="adminpassword"
        )
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )

    def test_unauthentified_user_index_view(self):
        response = self.client.get("/")
        self.assertRedirects(response, "/admin/", target_status_code=302)

    def test_regular_user_index_view(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get("/")
        self.assertRedirects(response, "/admin/", target_status_code=302)

    def test_admin_user_index_view(self):
        self.client.login(username="admin", password="adminpassword")
        response = self.client.get("/")
        self.assertRedirects(response, "/admin/", target_status_code=200)


class LogoutViewTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )

    def test_logout_user_view_clears_session_and_logs_out(self):
        self.client.login(username="testuser", password="testpassword")
        self.client.get("/logout/")

        self.assertFalse("_auth_user_id" in self.client.session)
        self.assertFalse("auth_user" in self.client.session)

    def test_logout_user_view_redirects_to_admin(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get("/logout/")

        self.assertRedirects(response, "/admin/", target_status_code=302)

    def test_unauthenticated_user_redirected_to_login(self):
        response = self.client.get("/logout/")
        self.assertRedirects(response, "/admin/", target_status_code=302)
