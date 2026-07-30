"""
Tests clôture forcée jobs MAGASIN.
"""
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from apps.inventory.constants import InventoryType
from apps.inventory.exceptions.job_exceptions import JobCreationError
from apps.inventory.services.magasin_jobs_force_complete_service import (
    MagasinJobsForceCompleteService,
)


class MagasinJobsForceCompleteServiceTests(SimpleTestCase):
    def setUp(self) -> None:
        self.service = MagasinJobsForceCompleteService()

    def test_empty_job_ids_raises(self):
        with self.assertRaises(JobCreationError):
            self.service.force_complete([])

    @patch.object(MagasinJobsForceCompleteService, "_resolve_product")
    @patch(
        "apps.inventory.services.magasin_jobs_force_complete_service.Job.objects"
    )
    def test_rejects_non_magasin_inventory(self, mock_jobs, mock_product):
        mock_product.return_value = Mock(id=1, Barcode="11111111111")
        inv = Mock(inventory_type=InventoryType.GENERAL)
        job = Mock(
            id=1,
            reference="JOB-0001",
            inventory=inv,
            warehouse_id=22,
            inventory_id=1,
        )
        mock_jobs.filter.return_value.select_related.return_value.prefetch_related.return_value = [
            job
        ]

        with self.assertRaises(JobCreationError) as ctx:
            self.service.force_complete([1])
        self.assertIn("MAGASIN", str(ctx.exception))

    @patch.object(MagasinJobsForceCompleteService, "_resolve_product")
    @patch(
        "apps.inventory.services.magasin_jobs_force_complete_service.Job.objects"
    )
    def test_rejects_tournant(self, mock_jobs, mock_product):
        mock_product.return_value = Mock(id=1, Barcode="11111111111")
        inv = Mock(inventory_type=InventoryType.TOURNANT)
        job = Mock(
            id=2,
            reference="JOB-0002",
            inventory=inv,
            warehouse_id=22,
            inventory_id=1,
        )
        mock_jobs.filter.return_value.select_related.return_value.prefetch_related.return_value = [
            job
        ]

        with self.assertRaises(JobCreationError) as ctx:
            self.service.force_complete([2])
        self.assertIn("MAGASIN", str(ctx.exception))
