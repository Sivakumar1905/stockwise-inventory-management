from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from inventory.models import Category


class AccountFlowTests(TestCase):
    def test_registration_creates_account_and_logs_in(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "storekeeper",
                "email": "store@example.com",
                "password1": "SafePass!7421",
                "password2": "SafePass!7421",
            },
        )
        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(User.objects.filter(username="storekeeper").exists())
        self.assertIn("_auth_user_id", self.client.session)
        self.assertTrue(
            Category.objects.filter(
                user__username="storekeeper", name="General"
            ).exists()
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_logout_requires_post(self):
        user = User.objects.create_user(username="storekeeper", password="SafePass!7421")
        self.client.force_login(user)
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 405)