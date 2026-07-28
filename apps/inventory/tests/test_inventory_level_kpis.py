"""
Tests KPIs inventaire (agrégation tous magasins).
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.inventory.constants import SettingStatus
from apps.inventory.models import Inventory, Job, Setting
from apps.inventory.services.kpis_service import KpisService
from apps.masterdata.models import Account, Warehouse


class InventoryLevelKpiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username='kpi_inv',
            password='pass12345',
            type='ADMIN',
        )
        self.client.force_authenticate(user=self.user)

        self.account = Account.objects.create(
            reference='ACC-KPI-INV',
            account_name='Compte KPI Inv',
            account_statuts='ACTIVE',
        )
        self.wh1 = Warehouse.objects.create(
            reference='WH-KPI-I1',
            warehouse_name='Magasin 1',
            warehouse_type='CENTRAL',
            status='ACTIVE',
        )
        self.wh2 = Warehouse.objects.create(
            reference='WH-KPI-I2',
            warehouse_name='Magasin 2',
            warehouse_type='CENTRAL',
            status='ACTIVE',
        )
        self.inventory = Inventory.objects.create(
            reference='INV-KPI-ALL',
            label='Inv KPI all warehouses',
            status='EN REALISATION',
            inventory_type='MAGASIN',
            date=timezone.now(),
        )
        Setting.objects.create(
            reference='SET-KPI-I1',
            account=self.account,
            warehouse=self.wh1,
            inventory=self.inventory,
            status=SettingStatus.LANCEE,
        )
        Setting.objects.create(
            reference='SET-KPI-I2',
            account=self.account,
            warehouse=self.wh2,
            inventory=self.inventory,
            status=SettingStatus.TERMINEE,
        )
        Job.objects.create(
            inventory=self.inventory, warehouse=self.wh1, status='TERMINE'
        )
        Job.objects.create(
            inventory=self.inventory, warehouse=self.wh2, status='ENTAME'
        )

    def test_service_nombre_jobs_all_warehouses(self):
        service = KpisService()
        result = service.compute_nombre_jobs_total(self.inventory.id, None)
        self.assertEqual(result['meta']['scope'], 'inventory')
        self.assertEqual(result['data']['nombre_jobs_total'], 2)

    def test_service_repartition_magasins(self):
        service = KpisService()
        result = service.compute_repartition_magasins_par_statut(self.inventory.id)
        data = result['data']['repartition_magasins_par_statut']
        self.assertEqual(data['total_magasins'], 2)
        self.assertEqual(data['by_status'][SettingStatus.LANCEE]['count'], 1)
        self.assertEqual(data['by_status'][SettingStatus.TERMINEE]['count'], 1)

    def test_api_inv_nombre_jobs_total(self):
        url = reverse(
            'inv-kpi-nombre-jobs-total',
            kwargs={'inventory_id': self.inventory.id},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['nombre_jobs_total'], 2)
        self.assertEqual(response.data['meta']['scope'], 'inventory')

    def test_api_inv_nombre_magasins(self):
        url = reverse(
            'inv-kpi-nombre-magasins',
            kwargs={'inventory_id': self.inventory.id},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['nombre_magasins'], 2)

    def test_api_inv_repartition_magasins(self):
        url = reverse(
            'inv-kpi-repartition-magasins-par-statut',
            kwargs={'inventory_id': self.inventory.id},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        by_status = response.data['data']['repartition_magasins_par_statut'][
            'by_status'
        ]
        self.assertEqual(by_status['LANCEE']['count'], 1)
        self.assertEqual(by_status['TERMINEE']['count'], 1)
