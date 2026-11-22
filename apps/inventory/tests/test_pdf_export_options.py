"""
Export PDF des jobs : options facultatives de l'API asynchrone
(counting_order, assignment_statuses, job_statuses) et filtre du repository.
"""
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.inventory.models import Assigment, Counting, Inventory, Job
from apps.inventory.repositories.pdf_repository import PDFRepository
from apps.masterdata.models import Warehouse
from apps.users.models import UserApp


class PdfExportOptionsTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserApp.objects.create_user(username='web_pdf', type='Web', password='x')
        warehouse = Warehouse.objects.create(
            reference='WH-P', warehouse_name='Magasin', warehouse_type='MAGASIN', status='ACTIVE')
        cls.inventory = Inventory.objects.create(
            label='PDF', date=timezone.now(), status='EN REALISATION',
            inventory_type='GENERAL', reference='INV-PDF')
        cls.job = Job.objects.create(
            status='TRANSFERT', warehouse=warehouse, inventory=cls.inventory, reference='JOB-P')
        cls.assignments = {}
        for order, status in ((1, 'TERMINE'), (2, 'TRANSFERT'), (3, 'PRET')):
            counting = Counting(inventory=cls.inventory, order=order, count_mode='par article')
            counting.reference = counting.generate_reference(Counting.REFERENCE_PREFIX)
            counting.save()
            assignment = Assigment(job=cls.job, counting=counting, status=status)
            assignment.reference = assignment.generate_reference(Assigment.REFERENCE_PREFIX)
            assignment.save()
            cls.assignments[order] = assignment

    # --------------------------------------------------------------- repository
    def test_default_returns_pret_and_transfert_of_all_countings(self):
        rows = PDFRepository().get_assignments_by_inventory(self.inventory)
        self.assertEqual(sorted(a.counting.order for a in rows), [2, 3])

    def test_counting_order_keeps_only_that_counting(self):
        rows = PDFRepository().get_assignments_by_inventory(self.inventory, counting_order=3)
        self.assertEqual([a.counting.order for a in rows], [3])

    def test_filled_sheets_use_terminated_assignments(self):
        rows = PDFRepository().get_assignments_by_inventory(
            self.inventory, assignment_statuses=['TERMINE'], job_statuses=[])
        self.assertEqual([a.counting.order for a in rows], [1])

    # --------------------------------------------------------------- API async
    def _post(self, body):
        client = APIClient()
        client.force_authenticate(user=self.user)
        with patch('apps.inventory.views.pdf_views.enqueue_inventory_jobs_pdf_task') as enqueue:
            enqueue.return_value.id = '00000000-0000-0000-0000-000000000001'
            enqueue.return_value.status = 'PENDING'
            response = client.post(
                f'/web/api/inventory/{self.inventory.id}/jobs/pdf/async/', body, format='json')
        return response, enqueue

    def test_async_start_passes_options_to_task(self):
        response, enqueue = self._post({
            'job': [self.job.id], 'counting_order': 3,
            'assignment_statuses': ['PRET', 'TRANSFERT'],
        })
        self.assertEqual(response.status_code, 202)
        kwargs = enqueue.call_args.kwargs
        self.assertEqual(kwargs['job_ids'], [self.job.id])
        self.assertEqual(kwargs['counting_order'], 3)
        self.assertEqual(kwargs['assignment_statuses'], ['PRET', 'TRANSFERT'])

    def test_async_start_without_options_keeps_defaults(self):
        response, enqueue = self._post({'job': [self.job.id]})
        self.assertEqual(response.status_code, 202)
        kwargs = enqueue.call_args.kwargs
        self.assertIsNone(kwargs['counting_order'])
        self.assertIsNone(kwargs['assignment_statuses'])
        self.assertIsNone(kwargs['job_statuses'])

    def test_async_start_rejects_invalid_status(self):
        response, enqueue = self._post({'assignment_statuses': ['NIMPORTE']})
        self.assertEqual(response.status_code, 400)
        enqueue.assert_not_called()

    def test_async_start_rejects_invalid_counting_order(self):
        response, enqueue = self._post({'counting_order': 0})
        self.assertEqual(response.status_code, 400)
        enqueue.assert_not_called()
