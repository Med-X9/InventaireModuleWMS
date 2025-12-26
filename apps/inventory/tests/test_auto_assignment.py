"""
Tests unitaires pour l'affectation automatique des jobs depuis InventoryLocationJob
"""
from django.test import TestCase
from unittest.mock import Mock, patch, MagicMock
from django.utils import timezone
from ..services.auto_assignment_service import AutoAssignmentService
from ..repositories.auto_assignment_repository import AutoAssignmentRepository
from ..models import Job, Counting, Assigment, Inventory
from apps.users.models import UserApp
from apps.masterdata.models import InventoryLocationJob


class AutoAssignmentRepositoryTest(TestCase):
    """
    Tests unitaires pour le repository AutoAssignmentRepository
    """
    
    def setUp(self):
        """
        Initialisation des tests
        """
        self.repository = AutoAssignmentRepository()
    
    @patch('apps.inventory.repositories.auto_assignment_repository.Inventory.objects.get')
    def test_get_inventory_by_id_success(self, mock_get):
        """
        Test de récupération d'un inventaire existant
        """
        mock_inventory = Mock(spec=Inventory)
        mock_get.return_value = mock_inventory
        
        result = self.repository.get_inventory_by_id(1)
        
        self.assertEqual(result, mock_inventory)
        mock_get.assert_called_once_with(id=1)
    
    @patch('apps.inventory.repositories.auto_assignment_repository.Inventory.objects.get')
    def test_get_inventory_by_id_not_found(self, mock_get):
        """
        Test de récupération d'un inventaire inexistant
        """
        mock_get.side_effect = Inventory.DoesNotExist
        
        result = self.repository.get_inventory_by_id(999)
        
        self.assertIsNone(result)
    
    @patch('apps.inventory.repositories.auto_assignment_repository.InventoryLocationJob.objects.filter')
    def test_get_location_jobs_by_inventory(self, mock_filter):
        """
        Test de récupération des location jobs par inventaire
        """
        mock_queryset = Mock()
        mock_filter.return_value.select_related.return_value = mock_queryset
        
        result = self.repository.get_location_jobs_by_inventory(1)
        
        self.assertEqual(result, mock_queryset)
        mock_filter.assert_called_once_with(inventaire_id=1, is_deleted=False)
    
    @patch('apps.inventory.repositories.auto_assignment_repository.UserApp.objects.filter')
    def test_get_teams_by_usernames(self, mock_filter):
        """
        Test de récupération des équipes par usernames
        """
        usernames = ['team1', 'team2']
        mock_queryset = Mock()
        mock_filter.return_value = mock_queryset
        
        result = self.repository.get_teams_by_usernames(usernames)
        
        self.assertEqual(result, mock_queryset)
        mock_filter.assert_called_once_with(
            username__in=usernames,
            type='Mobile',
            is_active=True
        )


class AutoAssignmentServiceTest(TestCase):
    """
    Tests unitaires pour le service AutoAssignmentService
    """
    
    def setUp(self):
        """
        Initialisation des tests
        """
        self.mock_repository = Mock(spec=AutoAssignmentRepository)
        self.service = AutoAssignmentService(repository=self.mock_repository)
    
    def test_extract_teams_from_location_jobs(self):
        """
        Test d'extraction des équipes depuis les location jobs
        """
        mock_location_job_1 = Mock(session_1='team1', session_2='team2')
        mock_location_job_2 = Mock(session_1='team1', session_2='team3')
        location_jobs = [mock_location_job_1, mock_location_job_2]
        
        result = self.service._extract_teams_from_location_jobs(location_jobs)
        
        self.assertEqual(result, {'team1', 'team2', 'team3'})
    
    def test_extract_teams_from_location_jobs_with_empty_sessions(self):
        """
        Test d'extraction des équipes avec des sessions vides
        """
        mock_location_job = Mock(session_1=None, session_2='')
        location_jobs = [mock_location_job]
        
        result = self.service._extract_teams_from_location_jobs(location_jobs)
        
        self.assertEqual(result, set())
    
    def test_validate_teams_exist(self):
        """
        Test de validation de l'existence des équipes
        """
        teams_list = ['team1', 'team2']
        mock_queryset = Mock()
        mock_queryset.values_list.return_value = ['team1', 'team2']
        
        self.mock_repository.get_teams_by_usernames.return_value = mock_queryset
        
        result = self.service._validate_teams_exist(teams_list)
        
        self.assertEqual(result, {'team1', 'team2'})
        self.mock_repository.get_teams_by_usernames.assert_called_once_with(teams_list)
    
    def test_group_location_jobs_by_job_reference(self):
        """
        Test de groupement des location jobs par référence de job
        """
        mock_location_job_1 = Mock(job='JOB001')
        mock_location_job_2 = Mock(job='JOB001')
        mock_location_job_3 = Mock(job='JOB002')
        location_jobs = [mock_location_job_1, mock_location_job_2, mock_location_job_3]
        
        result = self.service._group_location_jobs_by_job_reference(location_jobs)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result['JOB001']), 2)
        self.assertEqual(len(result['JOB002']), 1)
    
    def test_auto_assign_jobs_inventory_not_found(self):
        """
        Test d'affectation avec un inventaire inexistant
        """
        self.mock_repository.get_inventory_by_id.return_value = None
        
        result = self.service.auto_assign_jobs_from_location_jobs(999)
        
        self.assertFalse(result['success'])
        self.assertIn('Inventaire avec l\'ID 999 non trouvé', result['errors'])
    
    def test_auto_assign_jobs_no_location_jobs(self):
        """
        Test d'affectation sans location jobs
        """
        mock_inventory = Mock(spec=Inventory, id=1)
        mock_queryset = Mock()
        mock_queryset.exists.return_value = False
        
        self.mock_repository.get_inventory_by_id.return_value = mock_inventory
        self.mock_repository.get_location_jobs_by_inventory.return_value = mock_queryset
        
        result = self.service.auto_assign_jobs_from_location_jobs(1)
        
        self.assertFalse(result['success'])
        self.assertIn('Aucun InventoryLocationJob trouvé', result['errors'][0])
    
    def test_check_team_conflicts_with_conflicts(self):
        """
        Test de détection de conflits d'affectation
        """
        teams_list = ['team1', 'team2']
        mock_inventories = Mock()
        mock_inventories.exists.return_value = True
        
        mock_assignment_1 = Mock()
        mock_assignment_1.session.username = 'team1'
        mock_assignment_1.job.inventory.reference = 'INV001'
        
        mock_assignment_2 = Mock()
        mock_assignment_2.session.username = 'team1'
        mock_assignment_2.job.inventory.reference = 'INV002'
        
        mock_conflicting_assignments = Mock()
        mock_conflicting_assignments.exists.return_value = True
        mock_conflicting_assignments.__iter__ = Mock(return_value=iter([mock_assignment_1, mock_assignment_2]))
        
        self.mock_repository.get_active_general_inventories_excluding.return_value = mock_inventories
        self.mock_repository.get_conflicting_assignments.return_value = mock_conflicting_assignments
        
        result = self.service._check_team_conflicts(teams_list, 1)
        
        self.assertEqual(len(result), 1)
        self.assertIn('team1', result[0])
        self.assertIn('INV001', result[0])
        self.assertIn('INV002', result[0])
    
    def test_check_team_conflicts_no_conflicts(self):
        """
        Test de détection de conflits sans conflits
        """
        teams_list = ['team1', 'team2']
        mock_inventories = Mock()
        mock_inventories.exists.return_value = False
        
        self.mock_repository.get_active_general_inventories_excluding.return_value = mock_inventories
        
        result = self.service._check_team_conflicts(teams_list, 1)
        
        self.assertEqual(len(result), 0)


class AutoAssignmentViewTest(TestCase):
    """
    Tests unitaires pour la vue AutoAssignJobsFromInventoryLocationJobView
    
    Note: Ces tests nécessitent DRF APIClient pour tester les endpoints HTTP
    """
    
    def setUp(self):
        """
        Initialisation des tests
        """
        from rest_framework.test import APIClient
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        self.client = APIClient()
        
        # Créer un utilisateur pour l'authentification
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    @patch('apps.inventory.services.auto_assignment_service.AutoAssignmentService.auto_assign_jobs_from_location_jobs')
    def test_post_auto_assign_success(self, mock_auto_assign):
        """
        Test d'affectation automatique réussie
        """
        mock_auto_assign.return_value = {
            'success': True,
            'data': {
                'assignments_created_counting_1': 5,
                'assignments_updated_counting_1': 0,
                'assignments_created_counting_2': 5,
                'assignments_updated_counting_2': 0,
                'total_jobs': 5,
                'total_teams': 2,
                'teams': ['team1', 'team2'],
                'inventory_id': 1,
                'inventory_reference': 'INV001',
                'counting_1_order': 1,
                'counting_2_order': 2,
                'timestamp': timezone.now()
            },
            'message': 'Affectation automatique réussie'
        }
        
        response = self.client.post('/api/inventory/1/auto-assign-jobs-from-location-jobs/')
        
        self.assertEqual(response.status_code, 201)
        mock_auto_assign.assert_called_once_with(1)
    
    @patch('apps.inventory.services.auto_assignment_service.AutoAssignmentService.auto_assign_jobs_from_location_jobs')
    def test_post_auto_assign_failure(self, mock_auto_assign):
        """
        Test d'affectation automatique échouée
        """
        mock_auto_assign.return_value = {
            'success': False,
            'errors': ['Inventaire avec l\'ID 999 non trouvé'],
            'message': 'Erreurs de validation'
        }
        
        response = self.client.post('/api/inventory/999/auto-assign-jobs-from-location-jobs/')
        
        self.assertEqual(response.status_code, 404)
        mock_auto_assign.assert_called_once_with(999)

    def test_check_jobs_and_assignments_already_ready_with_blocked_jobs(self):
        """
        Test de validation des jobs avec statuts non autorisés (PRET, TRANSFERT, ENTAME, TERMINE)
        """
        # Créer des mocks pour les jobs et assignments
        mock_job_blocked = Mock(spec=Job, reference='JOB001', status='PRET')
        mock_job_not_blocked = Mock(spec=Job, reference='JOB002', status='AFFECTE')

        mock_assignment_blocked = Mock(spec=Assigment, status='ENTAME')
        mock_assignment_not_blocked = Mock(spec=Assigment, status='AFFECTE')

        mock_counting_1 = Mock(spec=Counting)
        mock_counting_2 = Mock(spec=Counting)

        # Mock du repository pour retourner les assignments
        self.mock_repository.get_assignments_by_job_and_countings.side_effect = [
            [mock_assignment_blocked],  # Pour JOB001 (blocked)
            [mock_assignment_not_blocked]  # Pour JOB002 (not blocked)
        ]

        jobs_by_ref_dict = {
            'JOB001': mock_job_blocked,
            'JOB002': mock_job_not_blocked
        }

        result = self.service._check_jobs_and_assignments_already_ready(
            jobs_by_ref_dict, mock_counting_1, mock_counting_2
        )

        # Vérifier que les erreurs sont détectées
        self.assertEqual(len(result), 2)
        self.assertIn('Les jobs suivants ont des statuts non autorisés pour l\'affectation automatique', result[0])
        self.assertIn('(PRET, TRANSFERT, ENTAME, TERMINE)', result[0])
        self.assertIn('JOB001', result[0])
        self.assertIn("L'affectation automatique est bloquée", result[1])

        # Vérifier que get_assignments_by_job_and_countings a été appelée
        self.assertEqual(self.mock_repository.get_assignments_by_job_and_countings.call_count, 2)

    def test_check_jobs_and_assignments_already_ready_with_different_blocked_statuses(self):
        """
        Test de validation des jobs avec différents statuts non autorisés
        """
        # Créer des mocks pour les jobs avec différents statuts non autorisés
        mock_job_pret = Mock(spec=Job, reference='JOB001', status='PRET')
        mock_job_transfert = Mock(spec=Job, reference='JOB002', status='TRANSFERT')
        mock_job_entame = Mock(spec=Job, reference='JOB003', status='ENTAME')
        mock_job_termine = Mock(spec=Job, reference='JOB004', status='TERMINE')
        mock_job_ok = Mock(spec=Job, reference='JOB005', status='AFFECTE')

        mock_counting_1 = Mock(spec=Counting)
        mock_counting_2 = Mock(spec=Counting)

        # Mock du repository pour retourner des assignments vides (pas d'assignments avec statuts bloquants)
        self.mock_repository.get_assignments_by_job_and_countings.return_value = []

        jobs_by_ref_dict = {
            'JOB001': mock_job_pret,
            'JOB002': mock_job_transfert,
            'JOB003': mock_job_entame,
            'JOB004': mock_job_termine,
            'JOB005': mock_job_ok
        }

        result = self.service._check_jobs_and_assignments_already_ready(
            jobs_by_ref_dict, mock_counting_1, mock_counting_2
        )

        # Vérifier que les erreurs sont détectées pour tous les statuts non autorisés
        self.assertEqual(len(result), 2)
        self.assertIn('Les jobs suivants ont des statuts non autorisés pour l\'affectation automatique', result[0])
        self.assertIn('JOB001', result[0])  # PRET
        self.assertIn('JOB002', result[0])  # TRANSFERT
        self.assertIn('JOB003', result[0])  # ENTAME
        self.assertIn('JOB004', result[0])  # TERMINE
        self.assertNotIn('JOB005', result[0])  # AFFECTE devrait être OK

    def test_check_jobs_and_assignments_already_ready_no_ready_jobs(self):
        """
        Test de validation quand aucun job n'est au statut PRET
        """
        # Créer des mocks pour les jobs et assignments non prêts
        mock_job_1 = Mock(spec=Job, reference='JOB001', status='AFFECTE')
        mock_job_2 = Mock(spec=Job, reference='JOB002', status='AFFECTE')

        mock_assignment_1 = Mock(spec=Assigment, status='AFFECTE')
        mock_assignment_2 = Mock(spec=Assigment, status='AFFECTE')

        mock_counting_1 = Mock(spec=Counting)
        mock_counting_2 = Mock(spec=Counting)

        # Mock du repository pour retourner les assignments
        self.mock_repository.get_assignments_by_job_and_countings.side_effect = [
            [mock_assignment_1],  # Pour JOB001
            [mock_assignment_2]   # Pour JOB002
        ]

        jobs_by_ref_dict = {
            'JOB001': mock_job_1,
            'JOB002': mock_job_2
        }

        result = self.service._check_jobs_and_assignments_already_ready(
            jobs_by_ref_dict, mock_counting_1, mock_counting_2
        )

        # Vérifier qu'aucune erreur n'est détectée
        self.assertEqual(len(result), 0)

        # Vérifier que get_assignments_by_job_and_countings a été appelée
        self.assertEqual(self.mock_repository.get_assignments_by_job_and_countings.call_count, 2)

    def test_auto_assign_jobs_with_blocked_jobs_blocks_assignment(self):
        """
        Test d'affectation automatique bloquée quand des jobs ont des statuts non autorisés
        """
        # Setup des mocks
        mock_inventory = Mock(spec=Inventory, id=1)
        mock_location_jobs = Mock()
        mock_location_jobs.exists.return_value = True

        mock_counting_1 = Mock(spec=Counting)
        mock_counting_2 = Mock(spec=Counting)

        mock_job_ready = Mock(spec=Job, reference='JOB001', status='PRET')

        # Mock des méthodes du repository
        self.mock_repository.get_inventory_by_id.return_value = mock_inventory
        self.mock_repository.get_location_jobs_by_inventory.return_value = mock_location_jobs
        self.mock_repository.get_counting_by_inventory_and_order.side_effect = [mock_counting_1, mock_counting_2]
        self.mock_repository.get_jobs_by_references_and_inventory.return_value = [mock_job_ready]

        # Mock de _extract_teams_from_location_jobs pour retourner une équipe valide
        with patch.object(self.service, '_extract_teams_from_location_jobs', return_value={'team1'}):
            # Mock de _validate_teams_exist pour retourner l'équipe
            with patch.object(self.service, '_validate_teams_exist', return_value={'team1'}):
                # Mock de _check_team_conflicts pour ne pas avoir de conflits
                with patch.object(self.service, '_check_team_conflicts', return_value=[]):
                    # Mock de _group_location_jobs_by_job_reference
                    with patch.object(self.service, '_group_location_jobs_by_job_reference', return_value={'JOB001': []}):
                        # Mock de get_assignments_by_job_and_countings pour retourner un assignment prêt
                        mock_assignment_ready = Mock(spec=Assigment, status='PRET')
                        self.mock_repository.get_assignments_by_job_and_countings.return_value = [mock_assignment_ready]

                        result = self.service.auto_assign_jobs_from_location_jobs(1)

                        # Vérifier que l'affectation est bloquée
                        self.assertFalse(result['success'])
                        self.assertIn('Les jobs suivants ont des statuts non autorisés pour l\'affectation automatique', str(result['errors']))
                        self.assertIn("L'affectation automatique est bloquée", str(result['errors']))

