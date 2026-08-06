"""
Tests pour l'API finished-assignments PDF (assignments TERMINE non imprimés).
"""
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.inventory.models import Assigment, Counting, Inventory, Job
from apps.inventory.services.assignment_service import AssignmentService
from apps.masterdata.models import Warehouse
from apps.users.models import UserApp


class FinishedUnprintedAssignmentsPdfTestCase(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = UserApp.objects.create_user(
            username='pdf-fin-user',
            type='Web',
            password='pass1234',
            email='pdf-fin@example.com',
        )
        self.client.force_authenticate(user=self.user)

        self.warehouse = Warehouse.objects.create(
            reference='WH-PDF-FIN',
            warehouse_name='WH PDF Fin',
            warehouse_type='CENTRAL',
            status='ACTIVE',
        )
        self.inventory = Inventory.objects.create(
            label='Inv PDF Fin',
            date=timezone.now(),
            status='EN REALISATION',
        )
        self.counting = Counting.objects.create(
            order=1,
            count_mode='en vrac',
            inventory=self.inventory,
        )
        self.job = Job.objects.create(
            status='TERMINE',
            warehouse=self.warehouse,
            inventory=self.inventory,
        )
        self.assignment = Assigment.objects.create(
            job=self.job,
            counting=self.counting,
            status='TERMINE',
            imprime=False,
        )
        self.url = reverse(
            'inventory-warehouse-finished-assignments-pdf-async',
            kwargs={
                'inventory_id': self.inventory.id,
                'warehouse_id': self.warehouse.id,
            },
        )

    def test_service_filters_termine_unprinted(self) -> None:
        service = AssignmentService()
        qs = service.get_finished_unprinted_assignments(
            self.inventory.id, self.warehouse.id
        )
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().id, self.assignment.id)

        self.assignment.imprime = True
        self.assignment.save(update_fields=['imprime'])
        self.assertEqual(
            service.get_finished_unprinted_assignments(
                self.inventory.id, self.warehouse.id
            ).count(),
            0,
        )

    def test_api_returns_202_when_assignments_exist(self) -> None:
        response = self.client.post(self.url, data={}, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_202_ACCEPTED,
            msg=response.data,
        )
        self.assertTrue(response.data['success'])
        self.assertIn('task_id', response.data)
        self.assertEqual(response.data['assignments_count'], 1)
        self.assertEqual(response.data['jobs_count'], 1)

    def test_api_returns_404_when_none(self) -> None:
        Assigment.objects.all().update(imprime=True)
        response = self.client.post(self.url, data={}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
