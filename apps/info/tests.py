from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.evacuation.models import EvacuationCenter
from apps.info.models import Info

User = get_user_model()


def _create_user(username, **extra_fields):
    return User.objects.create_user(
        username=username,
        password='secret1234',
        **extra_fields,
    )


def _create_center(name, owner, **overrides):
    data = {
        'name': name,
        'address': '123 Emergency Road',
        'latitude': 10.0,
        'longitude': 122.0,
        'capacity': 50,
        'status': 'available',
        'user': owner,
    }
    data.update(overrides)
    return EvacuationCenter.objects.create(**data)


class InfoCenterAssignmentTests(TestCase):
    """Staff check-ins must be attached to a specific evacuation center."""

    def setUp(self):
        self.staff = _create_user('creator', is_staff=True)
        self.other_staff = _create_user('other-creator', is_staff=True)
        self.center = _create_center('Sampaguita Evacuation Center', self.staff)
        self.other_center = _create_center('Rosal Evacuation Center', self.other_staff)
        self.client.force_login(self.staff)

    def _payload(self, **overrides):
        data = {
            'name': 'Juan Dela Cruz',
            'age': '30',
            'address': 'Barangay San Pedro',
            'email': '',
            'family_head': '',
        }
        data.update(overrides)
        return data

    def test_staff_can_assign_evacuee_to_own_center(self):
        response = self.client.post(
            reverse('info:info_save_ajax'),
            self._payload(evacuation_center=str(self.center.pk)),
        )

        self.assertEqual(response.status_code, 200)
        info = Info.objects.get(pk=response.json()['id'])
        self.assertEqual(info.evacuation_center_id, self.center.pk)

    def test_staff_cannot_assign_evacuee_to_an_unknown_center(self):
        response = self.client.post(
            reverse('info:info_save_ajax'),
            self._payload(evacuation_center='999999'),
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Info.objects.exists())

    def test_center_is_required_when_staff_manages_several_centers(self):
        response = self.client.post(reverse('info:info_save_ajax'), self._payload())

        self.assertEqual(response.status_code, 400)
        self.assertIn('evacuation center', response.json()['error'].lower())
        self.assertFalse(Info.objects.exists())

    def test_staff_can_move_evacuee_to_another_center(self):
        info = Info.objects.create(
            name='Juan Dela Cruz',
            age=30,
            address='Barangay San Pedro',
            evacuation_center=self.center,
            user=self.staff,
        )
        second_center = _create_center('Sampaguita Annex', self.staff)

        response = self.client.post(
            reverse('info:info_save_ajax'),
            self._payload(id=str(info.pk), evacuation_center=str(second_center.pk)),
        )

        self.assertEqual(response.status_code, 200)
        info.refresh_from_db()
        self.assertEqual(info.evacuation_center_id, second_center.pk)


class InfoSingleCenterAutoAssignTests(TestCase):
    """With exactly one center in the system, assign it without asking."""

    def setUp(self):
        self.staff = _create_user('solo-creator', is_staff=True)
        self.center = _create_center('Only Evacuation Center', self.staff)
        self.client.force_login(self.staff)

    def test_single_center_is_assigned_automatically(self):
        response = self.client.post(reverse('info:info_save_ajax'), {
            'name': 'Juan Dela Cruz',
            'age': '30',
            'address': 'Barangay San Pedro',
        })

        self.assertEqual(response.status_code, 200)
        info = Info.objects.get(pk=response.json()['id'])
        self.assertEqual(info.evacuation_center_id, self.center.pk)
