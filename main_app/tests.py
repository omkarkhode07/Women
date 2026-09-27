from django.test import TestCase
from .forms import UserCreateForm


class EmergencyContactCountTests(TestCase):
    def test_registration_form_accepts_valid_family_numbers(self):
        form = UserCreateForm(
            data={
                "username": "testuser1",
                "email": "testuser1@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "family_mobile_numbers": "+919999999999, +919988888888",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_registration_form_rejects_more_than_five_family_numbers(self):
        form = UserCreateForm(
            data={
                "username": "testuser2",
                "email": "testuser2@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "family_mobile_numbers": "+919999999999, +919988888888, +919977777777, +919966666666, +919955555555, +919944444444",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("family_mobile_numbers", form.errors)
