"""
Tests pour l'API de réaffectation des jobs (nouvelle API assign-jobs-manual)
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
import json

from ..models import Inventory, Job, Counting, Assigment, JobDetail, CountingDetail, NSerieInventory, EcartComptage, ComptageSequence
from apps.masterdata.models import Warehouse, Account, Location
from apps.users.models import UserApp

User = get_user_model()


class JobReassignmentAPITestCase(TestCase):
    """Tests pour l'API de réaffectation des jobs"""

    def setUp(self):
        """Configuration initiale pour les tests"""
        self.client = APIClient()

        # Créer un utilisateur pour l'authentification
        self.user = UserApp.objects.create_user(
            username='testuser',
            type='Web',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        # Utiliser des données simples ou existantes
        self.team1 = UserApp.objects.filter(type='Mobile').first()
        self.job = Job.objects.first()
        self.counting1 = Counting.objects.filter(order=1).first()
        self.counting2 = Counting.objects.filter(order=2).first()

        # Si les données n'existent pas, créer des données minimales
        if not self.team1:
            self.team1 = UserApp.objects.create(
                username='team1',
                type='Mobile',
                password='testpass123'
            )

        if not self.job:
            # Créer des données minimales si nécessaire
            try:
                account = Account.objects.create(
                    reference='TESTACC001',
                    account_name='Test Account',
                    account_statuts='ACTIVE'
                )
                warehouse = Warehouse.objects.create(
                    reference='TESTWH001',
                    warehouse_name='Test Warehouse',
                    warehouse_type='CENTRAL',
                    status='ACTIVE'
                )
                inventory = Inventory.objects.create(
                    reference='TESTINV001',
                    label='Test Inventory',
                    date=timezone.now(),
                    status='EN COURS'
                )
                self.job = Job.objects.create(
                    reference='TESTJOB001',
                    status='EN ATTENTE',
                    warehouse=warehouse,
                    inventory=inventory
                )
                self.counting1 = Counting.objects.create(
                    reference='TESTCNT001',
                    order=1,
                    count_mode='image stock',
                    inventory=inventory
                )
                self.counting2 = Counting.objects.create(
                    reference='TESTCNT002',
                    order=2,
                    count_mode='en vrac',
                    inventory=inventory
                )
            except Exception as e:
                print(f"Impossible de créer les données de test: {e}")
                # Utiliser les premières données disponibles
                self.job = Job.objects.first()
                if self.job:
                    self.counting1 = Counting.objects.filter(inventory=self.job.inventory, order=1).first()
                    self.counting2 = Counting.objects.filter(inventory=self.job.inventory, order=2).first()

    def test_reassign_team_success_without_complete(self):
        """Test de réaffectation réussie sans nettoyage complet"""
        # Vérifier que les données de test existent
        self.assertIsNotNone(self.job, "Job de test non trouvé")
        self.assertIsNotNone(self.team1, "Team1 de test non trouvé")
        self.assertIsNotNone(self.counting1, "Counting1 de test non trouvé")

        url = reverse('assign-jobs-manual')
        data = {
            'job_id': self.job.id,
            'team': self.team1.id,
            'counting_order': 1,
            'complete': False
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['job_id'], self.job.id)
        self.assertEqual(response.data['counting_order'], 1)
        self.assertFalse(response.data['complete_cleaned'])

        # Vérifier que l'affectation a été créée
        assignment = Assigment.objects.get(job=self.job, counting=self.counting1)
        self.assertEqual(assignment.session.id, self.team1.id)
        self.assertEqual(assignment.status, 'AFFECTE')

        # Vérifier que les données n'ont pas été nettoyées
        counting_details_count = CountingDetail.objects.filter(job=self.job).count()
        self.assertEqual(counting_details_count, 0)  # Pas de nettoyage

    def test_reassign_team_success_with_complete(self):
        """Test de réaffectation réussie avec nettoyage complet"""
        # Créer des données à nettoyer
        counting_detail = CountingDetail.objects.create(
            job=self.job,
            counting=self.counting1,
            location=self.location1,
            quantity_inventoried=10
        )

        n_serie = NSerieInventory.objects.create(
            counting_detail=counting_detail,
            n_serie='TEST001'
        )

        ecart_comptage = EcartComptage.objects.create(
            inventory=self.inventory,
            total_sequences=1,
            stopped_sequence=1
        )

        comptage_sequence = ComptageSequence.objects.create(
            ecart_comptage=ecart_comptage,
            counting_detail=counting_detail,
            sequence_number=1,
            quantity=10
        )

        # Créer une affectation existante
        existing_assignment = Assigment.objects.create(
            job=self.job,
            counting=self.counting1,
            session=self.team2,
            status='AFFECTE'
        )

        url = reverse('assign-jobs-manual')
        data = {
            'job_id': self.job.id,
            'team': self.team1.id,
            'counting_order': 1,
            'complete': True
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertTrue(response.data['complete_cleaned'])

        # Vérifier que les données ont été nettoyées
        self.assertEqual(CountingDetail.objects.filter(job=self.job).count(), 0)
        self.assertEqual(NSerieInventory.objects.filter(counting_detail=counting_detail).count(), 0)
        self.assertEqual(EcartComptage.objects.filter(inventory=self.inventory).count(), 0)
        self.assertEqual(ComptageSequence.objects.filter(ecart_comptage=ecart_comptage).count(), 0)

        # Vérifier que les statuts ont été mis à jour
        self.job_detail1.refresh_from_db()
        self.job_detail2.refresh_from_db()
        self.assertEqual(self.job_detail1.status, 'EN ATTENTE')
        self.assertEqual(self.job_detail2.status, 'EN ATTENTE')

        # Vérifier que l'affectation est à TRANSFERT après nettoyage
        existing_assignment.refresh_from_db()
        self.assertEqual(existing_assignment.status, 'TRANSFERT')

    def test_reassign_team_counting_order_2(self):
        """Test de réaffectation pour le comptage 2"""
        url = reverse('assign-jobs-manual')
        data = {
            'job_id': self.job.id,
            'team': self.team2.id,
            'counting_order': 2,
            'complete': False
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['counting_order'], 2)

        # Vérifier que l'affectation a été créée pour le bon comptage
        assignment = Assigment.objects.get(job=self.job, counting=self.counting2)
        self.assertEqual(assignment.session.id, self.team2.id)

    def test_reassign_team_job_status_update_transfert(self):
        """Test de mise à jour du statut du job à TRANSFERT"""
        # Créer une affectation existante à TRANSFERT
        Assigment.objects.create(
            job=self.job,
            counting=self.counting1,
            status='TRANSFERT'
        )

        url = reverse('assign-jobs-manual')
        data = {
            'job_id': self.job.id,
            'team': self.team1.id,
            'counting_order': 2,
            'complete': False
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier que le statut du job est mis à jour
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, 'TRANSFERT')

    def test_reassign_team_job_status_update_entame(self):
        """Test de mise à jour du statut du job à ENTAME"""
        # Créer une affectation existante à ENTAME
        Assigment.objects.create(
            job=self.job,
            counting=self.counting1,
            status='ENTAME'
        )

        url = reverse('assign-jobs-manual')
        data = {
            'job_id': self.job.id,
            'team': self.team1.id,
            'counting_order': 2,
            'complete': False
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier que le statut du job est mis à jour à ENTAME
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, 'ENTAME')

    def test_reassign_team_validation_error_terminated_assignment(self):
        """Test d'erreur de validation : assignement déjà terminé"""
        # Créer une affectation terminée
        Assigment.objects.create(
            job=self.job,
            counting=self.counting1,
            status='TERMINE'
        )

        url = reverse('assign-jobs-manual')
        data = {
            'job_id': self.job.id,
            'team': self.team1.id,
            'counting_order': 1,
            'complete': False
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('déjà terminé', response.data['error'])

    def test_reassign_team_invalid_job_id(self):
        """Test avec un job_id invalide"""
        url = reverse('assign-jobs-manual')
        data = {
            'job_id': 99999,  # ID inexistant
            'team': self.team1.id,
            'counting_order': 1,
            'complete': False
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('n\'existe pas', response.data['error'])

    def test_reassign_team_invalid_team_id(self):
        """Test avec un team_id invalide"""
        url = reverse('assign-jobs-manual')
        data = {
            'job_id': self.job.id,
            'team': 99999,  # ID inexistant
            'counting_order': 1,
            'complete': False
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('n\'existe pas', response.data['error'])

    def test_reassign_team_invalid_counting_order(self):
        """Test avec un counting_order invalide"""
        url = reverse('assign-jobs-manual')
        data = {
            'job_id': self.job.id,
            'team': self.team1.id,
            'counting_order': 3,  # Invalide, doit être 1 ou 2
            'complete': False
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('counting_order doit être 1 ou 2', ' | '.join(response.data['errors']))

    def test_reassign_team_missing_required_fields(self):
        """Test avec des champs obligatoires manquants"""
        url = reverse('assign-jobs-manual')
        data = {
            'job_id': self.job.id,
            'team': self.team1.id,
            # counting_order manquant
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_reassign_team_counting_not_found(self):
        """Test quand le comptage demandé n'existe pas"""
        # Supprimer le counting2 pour simuler un inventaire avec un seul comptage
        self.counting2.delete()

        url = reverse('assign-jobs-manual')
        data = {
            'job_id': self.job.id,
            'team': self.team1.id,
            'counting_order': 2,  # Demande le 2ème comptage qui n'existe pas
            'complete': False
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('non trouvé', response.data['error'])
