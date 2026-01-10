"""
Service pour l'affectation automatique des jobs depuis InventoryLocationJob
"""
import logging
from typing import Dict, List, Set, Optional
from django.db import transaction
from django.utils import timezone
from ..repositories.auto_assignment_repository import AutoAssignmentRepository
from ..models import Assigment

logger = logging.getLogger(__name__)


class AutoAssignmentService:
    """
    Service contenant la logique métier pour l'affectation automatique des jobs
    """
    
    # Statuts de jobs qui doivent être préservés lors de l'affectation
    PRESERVED_JOB_STATUSES = ['PRET', 'TRANSFERT', 'ENTAME', 'TERMINE', 'SAISIE MANUELLE']
    
    def __init__(self, repository: Optional[AutoAssignmentRepository] = None):
        """
        Initialise le service avec un repository
        
        Args:
            repository: Instance de AutoAssignmentRepository (injection de dépendance)
        """
        self.repository = repository or AutoAssignmentRepository()
    
    def auto_assign_jobs_from_location_jobs(self, inventory_id: int) -> Dict:
        """
        Effectue l'affectation automatique des jobs à partir des InventoryLocationJob
        
        Cette méthode :
        1. Valide l'inventaire et récupère les location jobs
        2. Extrait et valide les équipes
        3. Vérifie les conflits d'affectation
        4. Crée/met à jour les assignments avec transaction atomique
        
        Args:
            inventory_id: ID de l'inventaire
            
        Returns:
            Dict contenant le résultat de l'opération avec :
            - success: bool
            - data: Dict avec les détails (si succès)
            - errors: List[str] (si échec)
            - message: str
            
        Raises:
            Exception: En cas d'erreur inattendue
        """
        errors = []
        
        # Validation de l'inventaire
        inventory = self.repository.get_inventory_by_id(inventory_id)
        if not inventory:
            errors.append(f"Inventaire avec l'ID {inventory_id} non trouvé")
            return {
                'success': False,
                'errors': errors,
                'message': "Erreurs de validation"
            }
        
        # Récupération des location jobs
        location_jobs = self.repository.get_location_jobs_by_inventory(inventory_id)
        if not location_jobs.exists():
            errors.append(f"Aucun InventoryLocationJob trouvé pour l'inventaire {inventory_id}")
            return {
                'success': False,
                'errors': errors,
                'message': "Erreurs de validation"
            }
        
        # Extraction des équipes uniques
        teams_set = self._extract_teams_from_location_jobs(location_jobs)
        if not teams_set:
            errors.append("Aucune équipe trouvée dans les InventoryLocationJob")
        
        # Validation des équipes
        teams_list = list(teams_set) if teams_set else []
        if teams_list:
            existing_teams_set = self._validate_teams_exist(teams_list)
            missing_teams = teams_set - existing_teams_set
            
            if missing_teams:
                errors.append(
                    f"Équipes non trouvées dans UserApp (type Mobile) : {', '.join(sorted(missing_teams))}"
                )
        
        # Validation des comptages
        counting_1 = self.repository.get_counting_by_inventory_and_order(inventory_id, 1)
        counting_2 = self.repository.get_counting_by_inventory_and_order(inventory_id, 2)
        
        if not counting_1:
            errors.append(f"Comptage d'ordre 1 non trouvé pour l'inventaire {inventory_id}")
        
        if not counting_2:
            errors.append(f"Comptage d'ordre 2 non trouvé pour l'inventaire {inventory_id}")
        
        # Vérification des conflits d'affectation
        if teams_list:
            conflict_errors = self._check_team_conflicts(teams_list, inventory_id)
            errors.extend(conflict_errors)
        
        # Groupement des location jobs par référence de job
        jobs_by_reference = self._group_location_jobs_by_job_reference(location_jobs)
        
        # Validation des jobs existants
        job_references = list(jobs_by_reference.keys())
        jobs_by_ref_dict = {}
        
        if job_references:
            jobs = self.repository.get_jobs_by_references_and_inventory(
                job_references, 
                inventory_id
            )
            jobs_by_ref_dict = {job.reference: job for job in jobs}
            missing_job_refs = set(job_references) - set(jobs_by_ref_dict.keys())
            
            if missing_job_refs:
                errors.append(
                    f"Jobs non trouvés pour les références : {', '.join(sorted(missing_job_refs))}"
                )
        
        # Validation : vérifier si les jobs et leurs assignments sont déjà au statut PRET
        if job_references:
            ready_validation_errors = self._check_jobs_and_assignments_already_ready(
                jobs_by_ref_dict, counting_1, counting_2
            )
            errors.extend(ready_validation_errors)

        # Si des erreurs ont été collectées, les retourner
        if errors:
            return {
                'success': False,
                'errors': errors,
                'message': "Erreurs de validation détectées"
            }
        
        # Récupération des UserApp correspondants
        teams_userapp = {
            team.username: team 
            for team in self.repository.get_teams_by_usernames(teams_list)
        }
        
        # Effectuer l'affectation avec transaction atomique
        try:
            result = self._perform_assignments(
                jobs_by_reference,
                jobs_by_ref_dict,
                teams_userapp,
                counting_1,
                counting_2,
                inventory,
                teams_set
            )
            
            return {
                'success': True,
                'data': result,
                'message': (
                    f"Affectation automatique réussie : "
                    f"pour {result['total_jobs']} jobs"
                )
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affectation automatique : {str(e)}", exc_info=True)
            return {
                'success': False,
                'errors': [f"Erreur lors de l'affectation : {str(e)}"],
                'message': "Erreur lors de l'affectation automatique"
            }
    
    def _extract_teams_from_location_jobs(self, location_jobs) -> Set[str]:
        """
        Extrait les équipes uniques des location jobs
        
        Args:
            location_jobs: QuerySet d'InventoryLocationJob
            
        Returns:
            Set des usernames d'équipes
        """
        teams_set = set()
        for location_job in location_jobs:
            if location_job.session_1:
                teams_set.add(location_job.session_1.strip())
            if location_job.session_2:
                teams_set.add(location_job.session_2.strip())
        return teams_set
    
    def _validate_teams_exist(self, teams_list: List[str]) -> Set[str]:
        """
        Valide que les équipes existent dans UserApp
        
        Args:
            teams_list: Liste des usernames à valider
            
        Returns:
            Set des usernames existants
        """
        existing_teams = self.repository.get_teams_by_usernames(teams_list).values_list(
            'username', 
            flat=True
        )
        return set(existing_teams)
    
    def _check_team_conflicts(self, teams_list: List[str], inventory_id: int) -> List[str]:
        """
        Vérifie les conflits d'affectation pour les équipes

        NOTE: La vérification des conflits avec les autres inventaires GENERAL en cours
        a été désactivée. Les équipes peuvent désormais être affectées à plusieurs
        inventaires simultanément.

        Args:
            teams_list: Liste des usernames à vérifier
            inventory_id: ID de l'inventaire courant (à exclure)

        Returns:
            Liste des messages d'erreur de conflit (toujours vide)
        """
        # La vérification des conflits a été désactivée
        # Retourne toujours une liste vide pour permettre l'affectation simultanée
        return []

    def _check_jobs_and_assignments_already_ready(self, jobs_by_ref_dict: Dict, counting_1, counting_2) -> List[str]:
        """
        Vérifie si les jobs et leurs assignments ont des statuts non autorisés

        Les statuts non autorisés pour l'affectation automatique sont :
        PRET, TRANSFERT, ENTAME, TERMINE

        Si un job ou ses assignments pour les comptages 1 et 2 ont ces statuts,
        l'affectation automatique doit être bloquée.

        Args:
            jobs_by_ref_dict: Dict mapping référence -> instance de Job
            counting_1: Instance de Counting (ordre 1)
            counting_2: Instance de Counting (ordre 2)

        Returns:
            Liste des messages d'erreur pour les jobs avec statuts non autorisés
        """
        # Statuts non autorisés pour l'affectation automatique
        NON_AUTHORIZED_STATUSES = ['PRET', 'TRANSFERT', 'ENTAME', 'TERMINE']

        errors = []
        blocked_jobs = []

        for job_ref, job in jobs_by_ref_dict.items():
            # Vérifier si le job lui-même a un statut non autorisé
            if job.status in NON_AUTHORIZED_STATUSES:
                blocked_jobs.append(job_ref)
                continue

            # Vérifier les assignments pour les comptages 1 et 2
            assignments = self.repository.get_assignments_by_job_and_countings(job, [counting_1, counting_2])

            for assignment in assignments:
                if assignment.status in NON_AUTHORIZED_STATUSES:
                    blocked_jobs.append(job_ref)
                    break

        # Générer les messages d'erreur pour les jobs bloqués
        if blocked_jobs:
            errors.append(
                f"Les jobs suivants ont des statuts non autorisés pour l'affectation automatique "
                f"(PRET, TRANSFERT, ENTAME, TERMINE) : {', '.join(sorted(set(blocked_jobs)))}"
            )
            errors.append(
                "L'affectation automatique est bloquée car ces jobs ont des statuts avancés."
            )

        return errors

    def _group_location_jobs_by_job_reference(self, location_jobs) -> Dict:
        """
        Groupe les location jobs par référence de job
        
        Args:
            location_jobs: QuerySet d'InventoryLocationJob
            
        Returns:
            Dict[str, List] mapping référence -> liste de location jobs
        """
        jobs_by_reference = {}
        for location_job in location_jobs:
            if location_job.job:
                job_ref = location_job.job.strip()
                if job_ref not in jobs_by_reference:
                    jobs_by_reference[job_ref] = []
                jobs_by_reference[job_ref].append(location_job)
        return jobs_by_reference
    
    def _perform_assignments(
        self,
        jobs_by_reference: Dict,
        jobs_by_ref_dict: Dict,
        teams_userapp: Dict,
        counting_1,
        counting_2,
        inventory,
        teams_set: Set
    ) -> Dict:
        """
        Effectue les affectations avec transaction atomique
        
        Args:
            jobs_by_reference: Dict mapping référence -> liste de location jobs
            jobs_by_ref_dict: Dict mapping référence -> instance de Job
            teams_userapp: Dict mapping username -> instance de UserApp
            counting_1: Instance de Counting (ordre 1)
            counting_2: Instance de Counting (ordre 2)
            inventory: Instance d'Inventory
            teams_set: Set des usernames d'équipes
            
        Returns:
            Dict contenant les statistiques de l'opération
        """
        assignments_created_1 = []
        assignments_created_2 = []
        assignments_updated_1 = []
        assignments_updated_2 = []
        current_time = timezone.now()
        
        with transaction.atomic():
            # Parcourir chaque job et créer/mettre à jour les assignments
            for job_ref, location_jobs_list in jobs_by_reference.items():
                job = jobs_by_ref_dict[job_ref]
                
                # Utiliser les sessions du premier location_job
                first_location_job = location_jobs_list[0]
                
                # Assignment pour le comptage 1 avec session_1
                if first_location_job.session_1:
                    assignment_1_result = self._create_or_update_assignment(
                        job=job,
                        counting=counting_1,
                        session_username=first_location_job.session_1.strip(),
                        teams_userapp=teams_userapp,
                        current_time=current_time
                    )
                    
                    if assignment_1_result['created']:
                        assignments_created_1.append(assignment_1_result['assignment'].id)
                    elif assignment_1_result['updated']:
                        assignments_updated_1.append(assignment_1_result['assignment'].id)
                
                # Assignment pour le comptage 2 avec session_2
                if first_location_job.session_2:
                    assignment_2_result = self._create_or_update_assignment(
                        job=job,
                        counting=counting_2,
                        session_username=first_location_job.session_2.strip(),
                        teams_userapp=teams_userapp,
                        current_time=current_time
                    )
                    
                    if assignment_2_result['created']:
                        assignments_created_2.append(assignment_2_result['assignment'].id)
                    elif assignment_2_result['updated']:
                        assignments_updated_2.append(assignment_2_result['assignment'].id)
                
                # Mettre à jour le statut du job si nécessaire
                if job.status not in self.PRESERVED_JOB_STATUSES:
                    self.repository.update_job_status(
                        job=job,
                        status='AFFECTE',
                        affecte_date=current_time
                    )
        
        # Préparer les données de réponse
        return {
            'assignments_created_counting_1': len(assignments_created_1),
            'assignments_updated_counting_1': len(assignments_updated_1),
            'assignments_created_counting_2': len(assignments_created_2),
            'assignments_updated_counting_2': len(assignments_updated_2),
            'total_jobs': len(jobs_by_ref_dict),
            'total_teams': len(teams_set),
            'teams': sorted(list(teams_set)),
            'inventory_id': inventory.id,
            'inventory_reference': inventory.reference,
            'counting_1_order': 1,
            'counting_2_order': 2,
            'timestamp': current_time
        }
    
    def _create_or_update_assignment(
        self,
        job,
        counting,
        session_username: str,
        teams_userapp: Dict,
        current_time
    ) -> Dict:
        """
        Crée ou met à jour un assignment
        
        Args:
            job: Instance de Job
            counting: Instance de Counting
            session_username: Username de l'équipe
            teams_userapp: Dict mapping username -> UserApp
            current_time: Timestamp actuel
            
        Returns:
            Dict contenant :
            - assignment: Instance d'Assigment
            - created: bool
            - updated: bool
        """
        session_userapp = teams_userapp.get(session_username)
        
        if not session_userapp:
            return {'assignment': None, 'created': False, 'updated': False}
        
        assignment, created = self.repository.get_or_create_assignment(
            job=job,
            counting=counting,
            session=session_userapp,
            reference=Assigment().generate_reference(Assigment.REFERENCE_PREFIX),
            status='AFFECTE',
            affecte_date=current_time,
            date_start=current_time
        )
        
        updated = False
        
        if not created:
            # Déterminer le nouveau statut
            new_status = 'TRANSFERT' if assignment.status == 'ENTAME' else 'AFFECTE'
            transfert_date = current_time if assignment.status == 'ENTAME' else None
            
            # Mettre à jour l'assignment
            self.repository.update_assignment(
                assignment=assignment,
                session=session_userapp,
                status=new_status,
                affecte_date=current_time,
                date_start=current_time,
                transfert_date=transfert_date
            )
            updated = True
        
        return {
            'assignment': assignment,
            'created': created,
            'updated': updated
        }

