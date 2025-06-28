"""
Service pour l'affectation des jobs de comptage.
"""
from typing import Dict, Any, List
from django.utils import timezone
from django.db import transaction
from ..interfaces.assignment_interface import IAssignmentService
from ..repositories.assignment_repository import AssignmentRepository
from ..exceptions.assignment_exceptions import (
    AssignmentValidationError, 
    AssignmentBusinessRuleError,
    AssignmentSessionError
)
from ..models import Job, Counting, Assigment
from apps.users.models import UserApp

class AssignmentService(IAssignmentService):
    """Service pour l'affectation des jobs de comptage."""
    
    def __init__(self, repository: AssignmentRepository = None):
        self.repository = repository or AssignmentRepository()

    def assign_jobs(self, assignment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Affecte les jobs avec date_start et session
        
        Args:
            assignment_data: Données d'affectation contenant job_ids, counting_order, session_id, date_start
            
        Returns:
            Dict[str, Any]: Résultat de l'affectation
        """
        # Validation des données
        self.validate_assignment_data(assignment_data)
        
        job_ids = assignment_data['job_ids']
        counting_order = assignment_data['counting_order']
        session_id = assignment_data.get('session_id')
        date_start = assignment_data.get('date_start')
        
        with transaction.atomic():
            # Récupérer les jobs
            jobs = self.repository.get_jobs_by_ids(job_ids)
            
            # Vérifier que tous les jobs appartiennent au même inventaire
            inventory_ids = set(job.inventory_id for job in jobs)
            if len(inventory_ids) != 1:
                raise AssignmentValidationError("Tous les jobs doivent appartenir au même inventaire")
            
            inventory_id = list(inventory_ids)[0]
            
            # Récupérer le comptage
            counting = self.repository.get_counting_by_order_and_inventory(counting_order, inventory_id)
            if not counting:
                raise AssignmentValidationError(f"Comptage d'ordre {counting_order} non trouvé pour l'inventaire {inventory_id}")
            
            # Vérifier si on peut affecter une session à ce comptage
            if session_id and not self.can_assign_session_to_counting(counting_order, counting.count_mode):
                raise AssignmentSessionError(
                    f"Impossible d'affecter une session au comptage d'ordre {counting_order} "
                    f"avec le mode '{counting.count_mode}'. Les sessions ne sont autorisées que pour "
                    "les comptages 'en vrac' et 'par article' (pas pour 'image stock')."
                )
            
            # Vérifier que la session existe si fournie
            session = None
            if session_id:
                try:
                    session = UserApp.objects.get(id=session_id, role__name='Operateur')
                except UserApp.DoesNotExist:
                    raise AssignmentValidationError(f"Session avec l'ID {session_id} non trouvée ou n'est pas un opérateur")
            
            # Créer les affectations
            assignments_created = []
            for job in jobs:
                # Vérifier s'il existe déjà une affectation pour ce job
                existing_assignments = self.repository.get_existing_assignments_for_jobs([job.id])
                if existing_assignments:
                    raise AssignmentBusinessRuleError(f"Le job {job.reference} a déjà une affectation")
                
                # Créer l'affectation
                assignment_data = {
                    'job': job,
                    'counting': counting,
                    'date_start': date_start or timezone.now(),
                    'session': session
                }
                
                assignment = self.repository.create_assignment(assignment_data)
                assignments_created.append(assignment)
                
                # Mettre à jour le statut du job
                self.repository.update_job_status(job.id, 'AFFECTE', 'affecte_date')
            
            return {
                'success': True,
                'message': f"{len(assignments_created)} jobs affectés avec succès",
                'assignments_created': len(assignments_created),
                'counting_order': counting_order,
                'inventory_id': inventory_id
            }

    def validate_assignment_data(self, assignment_data: Dict[str, Any]) -> None:
        """
        Valide les données d'affectation
        
        Args:
            assignment_data: Données d'affectation à valider
            
        Raises:
            AssignmentValidationError: Si les données sont invalides
        """
        errors = []
        
        # Validation des champs obligatoires
        if not assignment_data.get('job_ids'):
            errors.append("La liste des IDs des jobs est obligatoire")
        
        if not assignment_data.get('counting_order'):
            errors.append("L'ordre du comptage est obligatoire")
        
        # Validation des types
        job_ids = assignment_data.get('job_ids', [])
        if not isinstance(job_ids, list) or not job_ids:
            errors.append("job_ids doit être une liste non vide")
        
        counting_order = assignment_data.get('counting_order')
        if counting_order and not isinstance(counting_order, int):
            errors.append("counting_order doit être un entier")
        
        if counting_order and counting_order not in [1, 2, 3]:
            errors.append("counting_order doit être 1, 2 ou 3")
        
        # Validation de la date_start si fournie
        date_start = assignment_data.get('date_start')
        if date_start and not isinstance(date_start, (str, type(timezone.now()))):
            errors.append("date_start doit être une date valide")
        
        if errors:
            raise AssignmentValidationError(" | ".join(errors))

    def can_assign_session_to_counting(self, counting_order: int, count_mode: str) -> bool:
        """
        Vérifie si on peut affecter une session à un comptage
        
        Règles métier :
        - Pour le mode "image stock" : pas d'affectation de session (automatique)
        - Pour les modes "en vrac" et "par article" : affectation de session autorisée
        
        Args:
            counting_order: Ordre du comptage
            count_mode: Mode de comptage
            
        Returns:
            bool: True si l'affectation est autorisée
        """
        # Le mode "image stock" ne nécessite pas d'affectation de session
        if count_mode == "image stock":
            return False
        
        # Les modes "en vrac" et "par article" peuvent avoir une session
        if count_mode in ["en vrac", "par article"]:
            return True
        
        # Mode non reconnu
        return False 