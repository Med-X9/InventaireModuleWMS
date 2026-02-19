"""
Tests pour l'API des jobs dont le 1er et le 2ème comptage sont terminés.
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.inventory.models import Inventory, Job, Assigment, Counting
from apps.masterdata.models import Warehouse

User = get_user_model()


class JobsBothCountingsAPITestCase(TestCase):
    """Tests pour GET /mobile/api/inventory/<id>/warehouse/<id>/jobs/both-countings-terminated/"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='mobile_test_user',
            password='testpass123',
            type='Mobile',
        )
        self.client.force_authenticate(user=self.user)

        self.warehouse = Warehouse.objects.create(
            reference='WH-TEST-JOB',
            warehouse_name='Entrepôt Test Jobs',
            warehouse_type='CENTRAL',
            status='ACTIVE',
        )
        self.inventory = Inventory.objects.create(
            label='Inventaire Test Jobs',
            status='EN REALISATION',
            date=timezone.now(),
        )
        self.counting_1 = Counting.objects.create(
            reference='CNT-TEST-JOB-1',
            order=1,
            count_mode='MODE1',
            inventory=self.inventory,
        )
        self.counting_2 = Counting.objects.create(
            reference='CNT-TEST-JOB-2',
            order=2,
            count_mode='MODE2',
            inventory=self.inventory,
        )

        self.job = Job.objects.create(
            inventory=self.inventory,
            warehouse=self.warehouse,
            status='TERMINE',
        )
        Assigment.objects.create(
            job=self.job,
            counting=self.counting_1,
            status='TERMINE',
        )
        Assigment.objects.create(
            job=self.job,
            counting=self.counting_2,
            status='TERMINE',
        )

    def test_jobs_both_countings_terminated_returns_200_and_list(self):
        url = (
            f"/mobile/api/inventory/{self.inventory.id}/warehouse/"
            f"{self.warehouse.id}/jobs/both-countings-terminated/"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('data', response.data)
        self.assertIn('jobs', response.data['data'])
        self.assertIn('count', response.data['data'])
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(len(response.data['data']['jobs']), 1)
        job_data = response.data['data']['jobs'][0]
        self.assertEqual(job_data['id'], self.job.id)
        self.assertEqual(job_data['reference'], self.job.reference)
        self.assertEqual(job_data['status'], 'TERMINE')
        self.assertNotIn('inventory', job_data)
        self.assertNotIn('warehouse', job_data)

    def test_jobs_both_countings_terminated_inventory_not_found_returns_404(self):
        url = (
            f"/mobile/api/inventory/99999/warehouse/"
            f"{self.warehouse.id}/jobs/both-countings-terminated/"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data.get('error_type'), 'INVENTORY_NOT_FOUND')

    def test_jobs_both_countings_terminated_warehouse_not_found_returns_404(self):
        url = (
            f"/mobile/api/inventory/{self.inventory.id}/warehouse/"
            f"99999/jobs/both-countings-terminated/"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data.get('error_type'), 'WAREHOUSE_NOT_FOUND')

    def test_jobs_both_countings_terminated_empty_list_when_no_matching_jobs(self):
        """Aucun job avec les deux comptages TERMINE pour un autre inventaire/warehouse."""
        other_warehouse = Warehouse.objects.create(
            reference='WH-OTHER',
            warehouse_name='Autre Entrepôt',
            warehouse_type='CENTRAL',
            status='ACTIVE',
        )
        other_inventory = Inventory.objects.create(
            label='Autre Inventaire',
            status='EN REALISATION',
            date=timezone.now(),
        )
        url = (
            f"/mobile/api/inventory/{other_inventory.id}/warehouse/"
            f"{other_warehouse.id}/jobs/both-countings-terminated/"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['count'], 0)
        self.assertEqual(response.data['data']['jobs'], [])
