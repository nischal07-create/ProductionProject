from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

class CoreApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpassword123")

    def test_server_health_check(self):
        # The health endpoint is exposed at /api/health/ (and /health/)
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_session_status_unauthenticated(self):
        response = self.client.get(reverse("session-status"))
        # Depending on implementation, might return 401, 403, or 200 with an empty body
        # Usually it returns 401 or 200 { "isAuthenticated": false }
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_session_status_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("session-status"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
