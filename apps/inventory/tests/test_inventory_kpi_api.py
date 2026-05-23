"""
Tests pour l'API KPI magasin — GET .../warehouses/<id>/kpis/
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.inventory.models import (
    Assigment,
    ComptageSequence,
    Counting,
    CountingDetail,
    EcartComptage,
    Inventory,
    Job,
    JobDetail,
    Setting,
)
from apps.masterdata.models import (
    Account,
    Location,
    LocationType,
    SousZone,
    Warehouse,
    Zone,
    ZoneType,
)
from apps.users.models import UserApp


class InventoryWarehouseKpiAPITestCase(APITestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username='kpi_tester',
            type='Web',
            password='password123',
        )
        self.client.force_authenticate(self.user)

        self.account = Account.objects.create(
            reference='ACC-KPI',
            account_name='Compte KPI',
            account_statuts='ACTIVE',
        )
        self.warehouse = Warehouse.objects.create(
            reference='WH-KPI',
            warehouse_name='Magasin KPI',
            warehouse_type='CENTRAL',
            status='ACTIVE',
        )
        self.inventory = Inventory.objects.create(
            label='Inventaire KPI',
            date=timezone.now(),
            status='EN REALISATION',
            inventory_type='GENERAL',
        )
        Setting.objects.create(
            reference='SET-KPI',
            account=self.account,
            warehouse=self.warehouse,
            inventory=self.inventory,
        )

        zone_type = ZoneType.objects.create(
            reference='ZT-KPI',
            type_name='Zone KPI',
            status='ACTIVE',
        )
        zone = Zone.objects.create(
            reference='Z-KPI',
            zone_name='Zone KPI',
            zone_type=zone_type,
            warehouse=self.warehouse,
            zone_status='ACTIVE',
        )
        sous_zone = SousZone.objects.create(
            reference='SZ-KPI',
            sous_zone_name='SZ KPI',
            zone=zone,
            sous_zone_status='ACTIVE',
        )
        loc_type = LocationType.objects.create(reference='LT-KPI', name='LT')
        self.location = Location.objects.create(
            reference='LOC-KPI',
            location_reference='KPI-01',
            sous_zone=sous_zone,
            location_type=loc_type,
        )

        self.counting_1 = Counting.objects.create(
            reference='CNT-1',
            inventory=self.inventory,
            order=1,
            count_mode='en vrac',
        )
        self.counting_2 = Counting.objects.create(
            reference='CNT-2',
            inventory=self.inventory,
            order=2,
            count_mode='en vrac',
        )

        self.job = Job.objects.create(
            reference='JOB-KPI-01',
            status='AFFECTE',
            warehouse=self.warehouse,
            inventory=self.inventory,
        )
        JobDetail.objects.create(
            reference='JBD-KPI-01',
            location=self.location,
            job=self.job,
        )

        self.mobile_user = UserApp.objects.create_user(
            username='equipe-kpi',
            type='Mobile',
            password='password123',
        )
        Assigment.objects.create(
            reference='ASS-KPI-1',
            status='TERMINE',
            job=self.job,
            counting=self.counting_1,
            session=self.mobile_user,
        )
        Assigment.objects.create(
            reference='ASS-KPI-2',
            status='ENTAME',
            job=self.job,
            counting=self.counting_2,
            session=self.mobile_user,
        )

        self.ecart = EcartComptage.objects.create(
            reference='ECT-KPI-1',
            inventory=self.inventory,
            resolved=False,
        )
        cd = CountingDetail.objects.create(
            reference='CD-KPI-1',
            quantity_inventoried=5,
            location=self.location,
            counting=self.counting_1,
            job=self.job,
        )
        ComptageSequence.objects.create(
            reference='CS-KPI-1',
            ecart_comptage=self.ecart,
            sequence_number=1,
            counting_detail=cd,
            quantity=5,
        )

    def _kpi_url(self, name: str) -> str:
        return reverse(
            name,
            kwargs={
                'inventory_id': self.inventory.id,
                'warehouse_id': self.warehouse.id,
            },
        )

    def test_kpi_nombre_jobs_total_endpoint(self) -> None:
        response = self.client.get(self._kpi_url('kpi-nombre-jobs-total'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertTrue(body['success'])
        self.assertEqual(body['meta']['kpi'], 'nombre-jobs-total')
        self.assertEqual(body['data']['nombre_jobs_total'], 1)

    def test_kpi_nombre_ecarts_endpoint(self) -> None:
        response = self.client.get(self._kpi_url('kpi-nombre-ecarts'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.json()['data']['nombre_ecarts'], 1)

    def test_kpi_nombre_equipes_endpoint(self) -> None:
        response = self.client.get(self._kpi_url('kpi-nombre-equipes'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['data']['nombre_equipes'], 1)

    def test_kpi_taux_termine_1er_comptage_par_equipe_endpoint(self) -> None:
        response = self.client.get(
            self._kpi_url('kpi-taux-termine-1er-comptage-par-equipe')
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        teams = response.json()['data']['taux_termine_1er_comptage_par_equipe']['teams']
        self.assertEqual(len(teams), 1)
        self.assertEqual(teams[0]['team_key'], f'session:{self.mobile_user.id}')

    def test_kpi_endpoint_inventory_not_found(self) -> None:
        url = reverse(
            'kpi-nombre-jobs-total',
            kwargs={'inventory_id': 99999, 'warehouse_id': self.warehouse.id},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
