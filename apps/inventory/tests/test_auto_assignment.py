"""
Tests unitaires pour l'affectation automatique des jobs depuis InventoryLocationJob
"""
from django.test import TestCase
from unittest.mock import Mock, patch, MagicMock
from django.utils import timezone
from django.urls import reverse
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
    
    def test_check_team_conflicts_disabled(self):
        """
        Test que la vérification des conflits est désactivée
        Même avec des inventaires actifs et des conflits simulés,
        la méthode retourne toujours une liste vide
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

        # La vérification des conflits est désactivée, donc toujours vide
        self.assertEqual(len(result), 0)
    
    def test_check_team_conflicts_always_empty(self):
        """
        Test que la vérification des conflits retourne toujours une liste vide
        Peu importe les paramètres d'entrée
        """
        teams_list = ['team1', 'team2']

        # Même avec des inventaires actifs simulés, pas de conflits détectés
        mock_inventories = Mock()
        mock_inventories.exists.return_value = True
        self.mock_repository.get_active_general_inventories_excluding.return_value = mock_inventories

        result = self.service._check_team_conflicts(teams_list, 1)

        # La vérification des conflits est désactivée, donc toujours vide
        self.assertEqual(len(result), 0)

        # Test avec liste vide aussi
        result_empty = self.service._check_team_conflicts([], 1)
        self.assertEqual(len(result_empty), 0)



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
            type='WEB',  # Type requis pour UserApp
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
        
        url = reverse('auto-assign-jobs-from-location-jobs', kwargs={'inventory_id': 1})
        response = self.client.post(url)
        
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
        
        url = reverse('auto-assign-jobs-from-location-jobs', kwargs={'inventory_id': 999})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 404)
        mock_auto_assign.assert_called_once_with(999)

