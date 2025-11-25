from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from ..models import (
    Inventory,
    Job,
    JobDetail,
    Counting,
    Assigment,
)
from apps.masterdata.models import (
    Account,
    Warehouse,
    ZoneType,
    Zone,
    SousZone,
    LocationType,
    Location,
)
from apps.users.models import UserApp


User = get_user_model()


class CountingLaunchAPITestCase(TestCase):
    """Tests d'intégration pour l'API de lancement des comptages."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='api-tester',
            type='Web',
            password='secure-password',
            email='tester@example.com',
            nom='Test',
            prenom='User',
        )
        self.client.force_authenticate(user=self.user)

        # Création des entités masterdata nécessaires
        self.account = Account.objects.create(
            reference='ACC-TEST',
            account_name='Compte Test',
            account_statuts='ACTIVE',
        )

        self.zone_type = ZoneType.objects.create(
            reference='ZT-TEST',
            type_name='Zone Type',
            status='ACTIVE',
        )

        self.warehouse = Warehouse.objects.create(
            reference='WH-TEST',
            warehouse_name='Entrepôt Test',
            warehouse_type='CENTRAL',
            status='ACTIVE',
        )

        self.zone = Zone.objects.create(
            reference='Z-TEST',
            warehouse=self.warehouse,
            zone_name='Zone A',
            zone_type=self.zone_type,
            zone_status='ACTIVE',
        )

        self.sous_zone = SousZone.objects.create(
            reference='SZ-TEST',
            sous_zone_name='Sous-zone A',
            zone=self.zone,
            sous_zone_status='ACTIVE',
        )

        self.location_type = LocationType.objects.create(
            reference='LT-TEST',
            name='Type A',
        )

        self.location = Location.objects.create(
            reference='LOC-TEST',
            location_reference='LOC-0001',
            sous_zone=self.sous_zone,
            location_type=self.location_type,
        )

        # Inventaire et comptages de base
        self.inventory = Inventory.objects.create(
            label='Inventaire Test',
            date=timezone.now(),
            status='EN PREPARATION',
        )

        self.counting1 = Counting.objects.create(
            order=1,
            count_mode='en vrac',
            reference='CNT-TEST-1',
            inventory=self.inventory,
        )
        self.counting2 = Counting.objects.create(
            order=2,
            count_mode='en vrac',
            reference='CNT-TEST-2',
            inventory=self.inventory,
        )
        self.counting3 = Counting.objects.create(
            order=3,
            count_mode='en vrac',
            reference='CNT-TEST-3',
            inventory=self.inventory,
        )

        self.job = Job.objects.create(
            status='VALIDE',
            warehouse=self.warehouse,
            inventory=self.inventory,
        )

        # Lier l'emplacement au job pour l'un des comptages existants
        JobDetail.objects.create(
            reference=JobDetail().generate_reference(JobDetail.REFERENCE_PREFIX),
            location=self.location,
            job=self.job,
            counting=self.counting1,
            status='TERMINE',
        )

        JobDetail.objects.create(
            reference=JobDetail().generate_reference(JobDetail.REFERENCE_PREFIX),
            location=self.location,
            job=self.job,
            counting=self.counting2,
            status='TERMINE',
        )

        self.assignment1 = Assigment.objects.create(
            reference=Assigment().generate_reference(Assigment.REFERENCE_PREFIX),
            job=self.job,
            counting=self.counting1,
            status='TERMINE',
        )
        self.assignment2 = Assigment.objects.create(
            reference=Assigment().generate_reference(Assigment.REFERENCE_PREFIX),
            job=self.job,
            counting=self.counting2,
            status='TERMINE',
        )

        self.session = UserApp.objects.create(
            username='mobile-session',
            type='Mobile',
            nom='Mobile',
            prenom='User',
        )

        self.url = reverse('job-launch-counting')

    def test_launch_third_counting_creates_assignment_and_jobdetail(self):
        """Le premier appel affecte le comptage d'ordre 3 existant."""
        payload = {
            'job_id': self.job.id,
            'location_id': self.location.id,
            'session_id': self.session.id,
        }

        response = self.client.post(self.url, data=payload, format='json')

        if response.status_code != status.HTTP_201_CREATED:
            self.fail(f"Response content: {response.content}")

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            msg=f"Response data: {response.data}",
        )
        self.assertTrue(response.data['success'])

        data = response.data['data']
        self.assertFalse(data['counting']['new_counting_created'])
        self.assertTrue(data['assignment']['created'])
        self.assertEqual(data['counting']['order'], 3)

        assignment = Assigment.objects.filter(job=self.job, counting=self.counting3).first()
        self.assertIsNotNone(assignment)
        self.assertEqual(assignment.session_id, self.session.id)
        self.assertEqual(assignment.status, 'TRANSFERT')

        job_detail = JobDetail.objects.filter(job=self.job, location=self.location, counting=self.counting3).first()
        self.assertIsNotNone(job_detail)

    def test_launch_fourth_counting_duplicates_configuration(self):
        """Un nouvel appel crée un comptage supplémentaire (ordre 4) en dupliquant l'ordre 3."""
        payload = {
            'job_id': self.job.id,
            'location_id': self.location.id,
            'session_id': self.session.id,
        }

        # Lancer d'abord le 3ème comptage
        first_response = self.client.post(self.url, data=payload, format='json')
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)

        job_detail_order3 = JobDetail.objects.get(job=self.job, location=self.location, counting=self.counting3)
        job_detail_order3.status = 'TERMINE'
        job_detail_order3.save()

        assignment_order3 = Assigment.objects.get(job=self.job, counting=self.counting3)
        assignment_order3.status = 'TERMINE'
        assignment_order3.save()

        initial_countings = Counting.objects.filter(inventory=self.inventory).count()

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            msg=f"Response data: {response.data}",
        )
        self.assertTrue(response.data['success'])

        data = response.data['data']
        self.assertTrue(data['counting']['new_counting_created'])
        self.assertTrue(data['assignment']['created'])
        self.assertEqual(data['counting']['order'], 4)

        updated_countings = Counting.objects.filter(inventory=self.inventory).count()
        self.assertEqual(updated_countings, initial_countings + 1)

        new_counting = Counting.objects.get(id=data['counting']['id'])
        self.assertEqual(new_counting.order, 4)
        self.assertEqual(new_counting.count_mode, self.counting3.count_mode)

        assignment = Assigment.objects.filter(job=self.job, counting=new_counting).first()
        self.assertIsNotNone(assignment)
        self.assertEqual(assignment.session_id, self.session.id)
        self.assertEqual(assignment.status, 'TRANSFERT')

        job_detail = JobDetail.objects.filter(job=self.job, location=self.location, counting=new_counting).first()
        self.assertIsNotNone(job_detail)

    def test_launch_fourth_counting_recreates_missing_order_three_jobdetail(self):
        """Le service recrée le JobDetail d'ordre 3 manquant si l'affectation est terminée."""
        payload = {
            'job_id': self.job.id,
            'location_id': self.location.id,
            'session_id': self.session.id,
        }

        # Lancer une première fois pour créer le comptage d'ordre 3
        first_response = self.client.post(self.url, data=payload, format='json')
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)

        job_detail_order3 = JobDetail.objects.get(job=self.job, location=self.location, counting=self.counting3)
        job_detail_order3.status = 'TERMINE'
        job_detail_order3.save()

        # Simuler un JobDetail d'ordre 3 supprimé alors que l'affectation est terminée
        JobDetail.objects.filter(job=self.job, location=self.location, counting=self.counting3).delete()
        assignment_order3 = Assigment.objects.get(job=self.job, counting=self.counting3)
        assignment_order3.status = 'TERMINE'
        assignment_order3.termine_date = timezone.now()
        assignment_order3.save()

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            msg=f"Response data: {response.data}",
        )
        self.assertTrue(response.data['success'])

        recreated_job_detail = JobDetail.objects.filter(
            job=self.job,
            location=self.location,
            counting=self.counting3,
        ).first()
        self.assertIsNotNone(recreated_job_detail)
        self.assertEqual(recreated_job_detail.status, 'TERMINE')

    def test_launch_third_counting_requires_previous_orders_completed(self):
        """Le 3ème comptage ne peut pas être lancé si le 1er ou le 2ème n'est pas terminé."""
        self.assignment1.status = 'AFFECTE'
        self.assignment1.save()
        job_detail_order1 = JobDetail.objects.get(job=self.job, location=self.location, counting=self.counting1)
        job_detail_order1.status = 'EN ATTENTE'
        job_detail_order1.save()

        payload = {
            'job_id': self.job.id,
            'location_id': self.location.id,
            'session_id': self.session.id,
        }

        response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('3ème comptage', response.data['message'])

    def test_launch_next_counting_requires_previous_order_completed(self):
        """Le comptage N ne peut pas être lancé si le comptage précédent n'est pas terminé."""
        payload = {
            'job_id': self.job.id,
            'location_id': self.location.id,
            'session_id': self.session.id,
        }

        first_response = self.client.post(self.url, data=payload, format='json')
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)

        second_response = self.client.post(self.url, data=payload, format='json')

        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ordre 3 n'est pas terminé", second_response.data['message'])

