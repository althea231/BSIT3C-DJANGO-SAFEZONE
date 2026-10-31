from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.evacuation.models import EvacuationCenter


def _create_user(username, **extra_fields):
    return get_user_model().objects.create_user(
        username=username,
        password='secret1234',
        **extra_fields,
    )


class DashboardAccessTests(TestCase):
    """Monitoring views are restricted to authorized creator / admin staff."""

    def test_dashboard_renders_for_staff_user(self):
        staff = _create_user('creator', is_staff=True)

        self.client.force_login(staff)
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')

    def test_dashboard_forbidden_for_authenticated_non_staff_user(self):
        user = _create_user('evacuee')

        self.client.force_login(user)
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 403)

    def test_dashboard_redirects_anonymous_user_to_login(self):
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))


class PublicMapAccessTests(TestCase):
    """Public disaster-mapping views must be reachable without authentication."""

    def test_public_evacuation_list_renders_for_anonymous_user(self):
        response = self.client.get(reverse('evacuation:evacuation_list'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'evacuation.html')

    def test_public_evacuation_list_ajax_rejects_no_login_required_for_anonymous_user(self):
        response = self.client.get(reverse('evacuation:evacuation_list_ajax'))

        self.assertEqual(response.status_code, 200)

    def test_public_evacuation_get_ajax_rejects_no_login_required_for_anonymous_user(self):
        response = self.client.get(reverse('evacuation:evacuation_get_ajax', args=[1]))

        self.assertEqual(response.status_code, 404)  # Unknown pk -> 404, not a login redirect.

    def test_public_center_evacuees_page_renders_for_anonymous_user(self):
        center = EvacuationCenter.objects.create(
            name='Test Evacuation Center',
            address='Test Address',
            latitude=0.0,
            longitude=0.0,
            capacity=10,
            status=EvacuationCenter.STATUS_AVAILABLE,
        )

        response = self.client.get(reverse('evacuation:center_evacuees_public', args=[center.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'public_evacuees.html')
        self.assertContains(response, center.name)

    def test_public_center_evacuees_page_404_for_unknown_center(self):
        response = self.client.get(reverse('evacuation:center_evacuees_public', args=[999]))

        self.assertEqual(response.status_code, 404)

    def test_home_renders_public_map_for_anonymous_user(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'evacuation.html')

    def test_home_renders_public_map_for_staff_user(self):
        staff = _create_user('creator-home', is_staff=True)

        self.client.force_login(staff)
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'evacuation.html')

    def test_public_evacuation_list_renders_for_staff_user(self):
        staff = _create_user('creator-evacuation', is_staff=True)

        self.client.force_login(staff)
        response = self.client.get(reverse('evacuation:evacuation_list'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'evacuation.html')
