"""Public / staff permission tests for the SafeZone evacuation check-ins."""

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


class PublicEvacueeSearchAjaxTests(TestCase):
    """The live public evacuee search must stay anonymous-friendly and safe."""

    def setUp(self):
        self.staff = _create_user('creator', is_staff=True)
        self.center = EvacuationCenter.objects.create(
            name='Sampaguita Evacuation Center',
            address='123 Emergency Road',
            latitude=10.0,
            longitude=122.0,
            capacity=50,
            current_occupancy=1,
            status='available',
            user=self.staff,
        )
        self.juan = Info.objects.create(
            name='Juan Dela Cruz',
            age=30,
            address='Barangay San Pedro',
            evacuation_center=self.center,
            user=self.staff,
        )
        self.maria = Info.objects.create(
            name='Maria Santos',
            age=28,
            address='Barangay San Miguel',
            evacuation_center=self.center,
            user=self.staff,
        )
        self.other_center = EvacuationCenter.objects.create(
            name='Rosal Evacuation Center',
            address='456 Safe Street',
            latitude=10.5,
            longitude=122.5,
            capacity=20,
            status='available',
            user=self.staff,
        )
        self.pedro = Info.objects.create(
            name='Pedro Reyes',
            age=40,
            address='Barangay Malinis',
            evacuation_center=self.other_center,
            user=self.staff,
        )

    def test_public_evacuee_search_ajax_requires_no_login(self):
        response = self.client.get(reverse('evacuation:public_evacuee_search_ajax'), {'q': 'Juan'})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['query'], 'Juan')
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['name'], 'Juan Dela Cruz')
        self.assertEqual(data['results'][0]['status'], 'Checked In')

    def test_public_evacuee_search_ajax_filters_by_name(self):
        response = self.client.get(reverse('evacuation:public_evacuee_search_ajax'), {'q': 'Maria'})

        data = response.json()
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['name'], 'Maria Santos')

    def test_public_evacuee_search_ajax_returns_empty_result_for_unknown_name(self):
        response = self.client.get(reverse('evacuation:public_evacuee_search_ajax'), {'q': 'Nobody'})

        data = response.json()
        self.assertEqual(data['results'], [])
        self.assertEqual(data['total'], 0)

    def test_public_evacuee_search_ajax_scopes_to_requested_center(self):
        response = self.client.get(
            reverse('evacuation:public_evacuee_search_ajax'),
            {'q': '', 'center_id': self.center.pk},
        )

        data = response.json()
        self.assertEqual(data['total'], 2)

    def test_public_evacuee_search_ajax_does_not_mix_centers_of_same_creator(self):
        # Regression test: two centers owned by the same creator must never
        # return the same evacuee list.
        response = self.client.get(
            reverse('evacuation:public_evacuee_search_ajax'),
            {'center_id': self.center.pk},
        )
        names = [result['name'] for result in response.json()['results']]

        self.assertEqual(sorted(names), ['Juan Dela Cruz', 'Maria Santos'])
        self.assertNotIn('Pedro Reyes', names)

        response = self.client.get(
            reverse('evacuation:public_evacuee_search_ajax'),
            {'center_id': self.other_center.pk},
        )
        names = [result['name'] for result in response.json()['results']]

        self.assertEqual(names, ['Pedro Reyes'])
        self.assertEqual(response.json()['results'][0]['center'], 'Rosal Evacuation Center')

    def test_public_evacuee_search_ajax_hides_personal_fields(self):
        response = self.client.get(reverse('evacuation:public_evacuee_search_ajax'), {'q': 'Juan'})

        result = response.json()['results'][0]
        self.assertNotIn('email', result)
        self.assertNotIn('address', result)
        self.assertNotIn('age', result)
        self.assertNotIn('family_head', result)


class PublicEvacueeListPageTests(TestCase):
    """The dedicated public check-in page exposes only transparency-safe data."""

    def setUp(self):
        self.staff = _create_user('creator', is_staff=True)
        self.center = EvacuationCenter.objects.create(
            name='Sampaguita Evacuation Center',
            address='123 Emergency Road',
            latitude=10.0,
            longitude=122.0,
            capacity=50,
            current_occupancy=2,
            status='available',
            contact_person='Kapitan Cruz',
            contact_number='09171234567',
            user=self.staff,
        )
        Info.objects.create(
            name='Juan Dela Cruz',
            age=30,
            address='Barangay San Pedro',
            email='juan@example.com',
            family_head='Pedro Dela Cruz',
            evacuation_center=self.center,
            user=self.staff,
        )
        Info.objects.create(
            name='Maria Santos',
            age=28,
            address='Barangay San Miguel',
            evacuation_center=self.center,
            user=self.staff,
        )

    def test_public_evacuee_list_renders_for_anonymous_user(self):
        response = self.client.get(
            reverse('evacuation:public_evacuee_list', args=[self.center.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'public_evacuees.html')
        self.assertContains(response, 'Juan Dela Cruz')
        self.assertContains(response, 'Maria Santos')
        self.assertContains(response, 'Checked In')

    def test_public_evacuee_list_filters_by_name(self):
        response = self.client.get(
            reverse('evacuation:public_evacuee_list', args=[self.center.pk]),
            {'q': 'Maria'},
        )

        self.assertContains(response, 'Maria Santos')
        self.assertNotContains(response, 'Juan Dela Cruz')

    def test_public_evacuee_list_only_shows_evacuees_of_selected_center(self):
        # Regression test for the reported bug: centers sharing a creator used
        # to display an identical list of evacuees.
        other_center = EvacuationCenter.objects.create(
            name='Rosal Evacuation Center',
            address='456 Safe Street',
            latitude=10.5,
            longitude=122.5,
            capacity=20,
            status='available',
            user=self.staff,
        )
        Info.objects.create(
            name='Pedro Reyes',
            age=40,
            address='Barangay Malinis',
            evacuation_center=other_center,
            user=self.staff,
        )

        response = self.client.get(
            reverse('evacuation:public_evacuee_list', args=[self.center.pk])
        )
        self.assertContains(response, 'Juan Dela Cruz')
        self.assertContains(response, 'Maria Santos')
        self.assertNotContains(response, 'Pedro Reyes')

        response = self.client.get(
            reverse('evacuation:public_evacuee_list', args=[other_center.pk])
        )
        self.assertContains(response, 'Pedro Reyes')
        self.assertNotContains(response, 'Juan Dela Cruz')
        self.assertNotContains(response, 'Maria Santos')

    def test_public_evacuee_list_hides_personal_details(self):
        response = self.client.get(
            reverse('evacuation:public_evacuee_list', args=[self.center.pk])
        )

        for private_value in (
            '09171234567',        # center contact number
            'Kapitan Cruz',       # center contact person
            '123 Emergency Road', # center exact address
            'Barangay San Pedro', # evacuee exact address
            'juan@example.com',   # evacuee e-mail address
            'Pedro Dela Cruz',    # family head
        ):
            self.assertNotContains(response, private_value)


class PublicEvacuationListPrivacyTests(TestCase):
    """Anonymous users must not see address / contact data on the center list."""

    def setUp(self):
        self.staff = _create_user('creator', is_staff=True)
        self.center = EvacuationCenter.objects.create(
            name='Sampaguita Evacuation Center',
            address='123 Emergency Road',
            latitude=10.0,
            longitude=122.0,
            capacity=50,
            status='available',
            contact_person='Kapitan Cruz',
            contact_number='09171234567',
            user=self.staff,
        )

    def test_anonymous_list_hides_address_and_contact_details(self):
        response = self.client.get(reverse('evacuation:evacuation_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sampaguita Evacuation Center')
        self.assertNotContains(response, '123 Emergency Road')
        self.assertNotContains(response, '09171234567')
        self.assertNotContains(response, 'Kapitan Cruz')

    def test_staff_list_still_shows_address_and_contact_details(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('evacuation:evacuation_list'))

        self.assertContains(response, '123 Emergency Road')
        self.assertContains(response, '09171234567')
        self.assertContains(response, 'Kapitan Cruz')

    def test_anonymous_list_links_to_public_evacuee_page(self):
        response = self.client.get(reverse('evacuation:evacuation_list'))

        self.assertContains(
            response,
            reverse('evacuation:public_evacuee_list', args=[self.center.pk]),
        )


class EvacueeReportCsvPermissionTests(TestCase):
    """Downloading the full evacuee report is strictly staff (creator) only."""

    def setUp(self):
        self.staff = _create_user('creator', is_staff=True)
        self.center = EvacuationCenter.objects.create(
            name='Sampaguita Evacuation Center',
            address='123 Emergency Road',
            latitude=10.0,
            longitude=122.0,
            capacity=50,
            current_occupancy=1,
            status='available',
            user=self.staff,
        )
        Info.objects.create(
            name='Juan Dela Cruz',
            age=30,
            address='Barangay San Pedro',
            evacuation_center=self.center,
            user=self.staff,
        )

    def test_evacuee_report_csv_redirects_anonymous_user_to_login(self):
        response = self.client.get(reverse('evacuation:evacuee_report_csv'))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))

    def test_evacuee_report_csv_forbidden_for_authenticated_non_staff_user(self):
        evacuee = _create_user('evacuee')
        self.client.force_login(evacuee)
        response = self.client.get(reverse('evacuation:evacuee_report_csv'))

        self.assertEqual(response.status_code, 403)

    def test_evacuee_report_csv_returns_csv_for_staff_user(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('evacuation:evacuee_report_csv'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('Evacuee Name', response.content.decode('utf-8'))
